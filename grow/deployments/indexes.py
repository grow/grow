"""Indexes for tracking the changes to pods across deployments and builds."""

import datetime
import logging
import sys
import traceback
import ConfigParser
import progressbar
import texttable
from grow.common import progressbar_non
from grow.common import utils as common_utils
from protorpc import protojson
from . import messages
from . import utils

if common_utils.is_appengine():
    # pylint: disable=invalid-name
    pool = None
else:
    from multiprocessing import pool


class Error(Exception):
    pass


class CorruptIndexError(Error):
    pass


class DeploymentError(Error):
    """Errors that occured during the rendering."""

    def __init__(self, message, err, err_tb):
        super(DeploymentError, self).__init__(message)
        self.err = err
        self.err_tb = err_tb


class DeploymentErrors(Error):
    """Errors that occured during the deployment."""

    def __init__(self, message, errors):
        super(DeploymentErrors, self).__init__(message)
        self.errors = errors


class Diff(object):
    POOL_SIZE = 10  # Thread pool size for applying a diff.
    GIT_LOG_MAX = 25

    @classmethod
    def is_empty(cls, diff):
        return not diff.adds and not diff.deletes and not diff.edits

    @classmethod
    def _format_author(cls, author, include_email=True):
        if not author:
            return ''
        author_name = author.name
        author_email = author.email
        if isinstance(author_name, unicode):
            author_name = author_name.encode('utf-8')
        if isinstance(author_email, unicode):
            author_email = author_email.encode('utf-8')
        if include_email:
            return '{} <{}>'.format(author_name, author_email)
        return author_name

    @classmethod
    def _make_diff_row(cls, color, label, message):
        label = texttable.get_color_string(color, label)
        path = texttable.get_color_string(
            texttable.bcolors.WHITE, message.path)
        formatted_author = cls._format_author(message.deployed_by, True)
        deployed = str(message.deployed).split('.')[0][
            :-3] if message.deployed else ''
        return [label, path, deployed, formatted_author]

    @classmethod
    def pretty_print(cls, diff):
        last_commit = diff.indexes[0].commit
        new_commit = diff.indexes[1].commit
        last_index = diff.indexes[0]
        new_index = diff.indexes[1]

        table = texttable.Texttable(max_width=0)
        table.set_deco(texttable.Texttable.HEADER)
        rows = []
        rows.append(['Action', 'Path', 'Last deployed', 'By'])
        file_rows = []
        for add in diff.adds:
            file_rows.append(cls._make_diff_row(
                texttable.bcolors.GREEN, 'add', add))
        for edit in diff.edits:
            file_rows.append(cls._make_diff_row(
                texttable.bcolors.PURPLE, 'edit', edit))
        for delete in diff.deletes:
            file_rows.append(cls._make_diff_row(
                texttable.bcolors.RED, 'delete', delete))
        file_rows.sort(key=lambda row: row[1])
        rows += file_rows
        table.add_rows(rows)
        logging.info('\n' + table.draw() + '\n')
        if last_index.deployed and last_index.deployed_by:
            logging.info('Last deployed: {} by {}'.format(
                last_index.deployed, cls._format_author(last_index.deployed_by)))
        last_commit_sha = last_commit.sha if last_commit else ''
        new_commit_sha = new_commit.sha if new_commit else ''
        if new_index.deployed_by:
            between_commits = '{}..{}'.format(
                last_commit_sha[:7],
                new_commit_sha[:7])
            if new_commit:
                if new_commit.has_unstaged_changes:
                    between_commits += ' (with unstaged changes)'
            else:
                between_commits += ' (initial commit)'
            logging.info('Diff: {} as {}'.format(
                between_commits, new_index.deployed_by.email))
        if diff.what_changed:
            logging.info(diff.what_changed + '\n')
        if diff.is_partial:
            logging.info(
                '  Note: Partial diffs do not include changes that remove files.\n')

    @classmethod
    def create(cls, index, theirs, repo=None, is_partial=False):
        git = common_utils.get_git()
        diff = messages.DiffMessage()
        diff.is_partial = is_partial
        diff.indexes = []
        diff.indexes.append(theirs or messages.IndexMessage())
        diff.indexes.append(index or messages.IndexMessage())

        index_paths_to_shas = {}
        their_paths_to_shas = {}

        for file_message in index.files:
            index_paths_to_shas[file_message.path] = file_message.sha
        for file_message in theirs.files:
            their_paths_to_shas[file_message.path] = file_message.sha

        for path, sha in index_paths_to_shas.iteritems():
            if path in their_paths_to_shas:
                if index_paths_to_shas[path] == their_paths_to_shas[path]:
                    file_message = messages.FileMessage()
                    file_message.path = path
                    file_message.deployed = theirs.deployed
                    file_message.deployed_by = theirs.deployed_by
                    diff.nochanges.append(file_message)
                else:
                    file_message = messages.FileMessage()
                    file_message.path = path
                    file_message.deployed = theirs.deployed
                    file_message.deployed_by = theirs.deployed_by
                    diff.edits.append(file_message)
                del their_paths_to_shas[path]
            else:
                file_message = messages.FileMessage()
                file_message.path = path
                diff.adds.append(file_message)

        # When doing partial diffs we do not have enough information to know
        # which files have been deleted.
        if not is_partial:
            for path, sha in their_paths_to_shas.iteritems():
                file_message = messages.FileMessage()
                file_message.path = path
                file_message.deployed = theirs.deployed
                file_message.deployed_by = theirs.deployed_by
                diff.deletes.append(file_message)

        # What changed in the pod between deploy commits.
        if (repo is not None and index.commit and index.commit.sha and theirs.commit
                and theirs.commit.sha):
            try:
                what_changed = repo.git.log(
                    '--date=short',
                    '--pretty=format:[%h] %ad <%ae> %s',
                    '{}..{}'.format(theirs.commit.sha, index.commit.sha))
                if isinstance(what_changed, unicode):
                    what_changed = what_changed.encode('utf-8')
                diff.what_changed = what_changed.decode('utf-8')
            except git.GitCommandError:
                logging.info('Unable to determine changes between deploys.')

        # If on the original deploy show commit log messages only.
        elif (repo is not None
              and index.commit and index.commit.sha):
            what_changed = repo.git.log(
                '--date=short',
                '--pretty=format:[%h] %ad <%ae> %s')
            if isinstance(what_changed, unicode):
                what_changed = what_changed.encode('utf-8')
            diff.what_changed = what_changed.decode('utf-8')

        return diff

    @classmethod
    def to_string(cls, message):
        return protojson.encode_message(message)

    @classmethod
    def apply(cls, message, paths_to_rendered_doc, write_func, batch_write_func, delete_func,
              threaded=True, batch_writes=False):
        if pool is None:
            text = 'Deployment is unavailable in this environment.'
            raise common_utils.UnavailableError(text)
        apply_errors = []
        thread_pool = None
        if threaded:
            thread_pool = pool.ThreadPool(cls.POOL_SIZE)
        diff = message
        num_files = len(diff.adds) + len(diff.edits) + len(diff.deletes)
        text = 'Deploying: %(value)d/{} (in %(time_elapsed).9s)'
        widgets = [progressbar.FormatLabel(text.format(num_files))]
        progress = progressbar_non.create_progressbar(
            "Deploying...", widgets=widgets, max_value=num_files)

        def run_func(kwargs):
            """Run an arbitrary function."""
            try:
                kwargs['func'](*kwargs['args'])
                return True
            # pylint: disable=broad-except
            except Exception as err:
                _, _, err_tb = sys.exc_info()
                return DeploymentError("Error deploying {}".format(kwargs['args']), err, err_tb)

        if batch_writes:
            writes_paths_to_rendered_doc = {}
            for file_message in diff.adds:
                writes_paths_to_rendered_doc[file_message.path] = \
                    paths_to_rendered_doc[file_message.path]
            for file_message in diff.edits:
                writes_paths_to_rendered_doc[file_message.path] = \
                    paths_to_rendered_doc[file_message.path]
            deletes_paths = [
                file_message.path for file_message in diff.deletes]
            if writes_paths_to_rendered_doc:
                batch_write_func(writes_paths_to_rendered_doc)
            if deletes_paths:
                delete_func(deletes_paths)
        else:
            progress.start()
            threaded_args = []

            for file_message in diff.adds:
                rendered_doc = paths_to_rendered_doc[file_message.path]
                threaded_args.append({
                    'func': write_func,
                    'args': (rendered_doc,),
                })
            for file_message in diff.edits:
                rendered_doc = paths_to_rendered_doc[file_message.path]
                threaded_args.append({
                    'func': write_func,
                    'args': (rendered_doc,),
                })
            for file_message in diff.deletes:
                threaded_args.append({
                    'func': delete_func,
                    'args': (file_message.path,),
                })

            if threaded:
                results = thread_pool.imap_unordered(run_func, threaded_args)
                for result in results:
                    if isinstance(result, Exception):
                        apply_errors.append(result)
                    progress.update(progress.value + 1)
            else:
                for kwargs in threaded_args:
                    try:
                        kwargs['func'](*kwargs['args'])
                        progress.update(progress.value + 1)
                    except DeploymentError as err:
                        apply_errors.append(err)

        if threaded:
            thread_pool.close()
            thread_pool.join()
        if not batch_writes:
            progress.finish()

        if apply_errors:
            for error in apply_errors:
                print error.message
                print error.err
                traceback.print_tb(error.err_tb)
                print ''
            text = 'There were {} errors during deployment.'
            raise DeploymentErrors(text.format(
                len(apply_errors)), apply_errors)

    @classmethod
    def stream(cls, theirs, content_generator, repo=None, is_partial=False):
        """Render the content and create a diff passing on only the changed content."""
        index = Index.create()
        if repo:
            Index.add_repo(index, repo)
        paths_to_rendered_doc = {}
        git = common_utils.get_git()
        diff = messages.DiffMessage()
        diff.is_partial = is_partial
        diff.indexes = []
        diff.indexes.append(theirs or messages.IndexMessage())
        diff.indexes.append(index or messages.IndexMessage())

        index_paths_to_shas = {}
        their_paths_to_shas = {}

        for file_message in theirs.files:
            their_paths_to_shas[file_message.path] = file_message.sha

        for rendered_doc in content_generator:
            path = rendered_doc.path
            index_paths_to_shas[path] = Index.add_file(index, rendered_doc).sha

            if path in their_paths_to_shas:
                if index_paths_to_shas[path] == their_paths_to_shas[path]:
                    file_message = messages.FileMessage()
                    file_message.path = path
                    file_message.deployed = theirs.deployed
                    file_message.deployed_by = theirs.deployed_by
                    diff.nochanges.append(file_message)
                else:
                    file_message = messages.FileMessage()
                    file_message.path = path
                    file_message.deployed = theirs.deployed
                    file_message.deployed_by = theirs.deployed_by
                    diff.edits.append(file_message)
                    paths_to_rendered_doc[path] = rendered_doc
                del their_paths_to_shas[path]
            else:
                file_message = messages.FileMessage()
                file_message.path = path
                diff.adds.append(file_message)
                paths_to_rendered_doc[path] = rendered_doc

        # When doing partial diffs we do not have enough information to know
        # which files have been deleted.
        if not is_partial:
            for path, _ in their_paths_to_shas.iteritems():
                file_message = messages.FileMessage()
                file_message.path = path
                file_message.deployed = theirs.deployed
                file_message.deployed_by = theirs.deployed_by
                diff.deletes.append(file_message)

        # What changed in the pod between deploy commits.
        if (repo is not None and index.commit and index.commit.sha and theirs.commit
                and theirs.commit.sha):
            try:
                what_changed = repo.git.log(
                    '--date=short',
                    '--pretty=format:[%h] %ad <%ae> %s',
                    '{}..{}'.format(theirs.commit.sha, index.commit.sha))
                if isinstance(what_changed, unicode):
                    what_changed = what_changed.encode('utf-8')
                diff.what_changed = what_changed.decode('utf-8')
            except git.GitCommandError:
                logging.info('Unable to determine changes between deploys.')

        # If on the original deploy show commit log messages only.
        elif (repo is not None
              and index.commit and index.commit.sha):
            what_changed = repo.git.log(
                '--date=short',
                '--pretty=format:[%h] %ad <%ae> %s')
            if isinstance(what_changed, unicode):
                what_changed = what_changed.encode('utf-8')
            changed_lines = what_changed.splitlines()
            num_lines = len(changed_lines)
            if num_lines > cls.GIT_LOG_MAX:
                changed_lines = changed_lines[:cls.GIT_LOG_MAX]
                changed_lines.append(
                    ' ... +{} more commits.'.format(num_lines-cls.GIT_LOG_MAX))
                what_changed = '\n'.join(changed_lines)
            diff.what_changed = what_changed.decode('utf-8')

        return diff, index, paths_to_rendered_doc


class Index(object):

    @classmethod
    def create(cls, paths_to_rendered_doc=None):
        message = messages.IndexMessage()
        message.deployed = datetime.datetime.now()
        message.files = []
        if paths_to_rendered_doc is None:
            return message
        for _, rendered_doc in paths_to_rendered_doc.iteritems():
            cls.add_file(message, rendered_doc)
        return message

    @classmethod
    def add_file(cls, message, rendered_doc):
        pod_path = '/' + rendered_doc.path.lstrip('/')
        file_message = messages.FileMessage(
            path=pod_path, sha=rendered_doc.hash)
        message.files.append(file_message)
        return file_message

    @classmethod
    def add_repo(cls, message, repo):
        config = repo.config_reader()
        try:
            message.deployed_by = messages.AuthorMessage(
                name=config.get('user', 'name'),
                email=config.get('user', 'email'))
        except (ConfigParser.NoSectionError, ConfigParser.NoOptionError):
            logging.warning("Couldn't find user info in repository config.")
        try:
            message.commit = utils.create_commit_message(repo)
        except utils.NoGitHeadError as e:
            logging.warning(e)
        return message

    @classmethod
    def to_string(cls, message):
        return protojson.encode_message(message)

    @classmethod
    def from_string(cls, content):
        return protojson.decode_message(messages.IndexMessage, content)
