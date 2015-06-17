from . import messages
from protorpc import protojson
import ConfigParser
import datetime
import git
import hashlib
import logging
import progressbar
import texttable
import threading


class Error(Exception):
  pass


class CorruptIndexError(Error):
  pass


class ProgressBarThread(threading.Thread):

  def __init__(self, bar, enabled, *args, **kwargs):
    self.bar = bar
    self.enabled = enabled
    super(ProgressBarThread, self).__init__(*args, **kwargs)

  def run(self):
    super(ProgressBarThread, self).run()
    if self.enabled:
      self.bar.update(self.bar.currval + 1)


class Diff(object):

  @classmethod
  def is_empty(cls, diff):
    return not diff.adds and not diff.deletes and not diff.edits

  @classmethod
  def _format_author(cls, author, include_email=True):
    if include_email:
      return '{} <{}>'.format(author.name, author.email) if author else ''
    return author.name if author else ''

  @classmethod
  def _make_diff_row(cls, color, label, message):
    label = texttable.get_color_string(color, label)
    path = texttable.get_color_string(texttable.bcolors.WHITE, message.path)
    formatted_author = cls._format_author(message.deployed_by, True)
    deployed = str(message.deployed).split('.')[0][:-3] if message.deployed else ''
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
      file_rows.append(cls._make_diff_row(texttable.bcolors.GREEN, 'add', add))
    for edit in diff.edits:
      file_rows.append(cls._make_diff_row(texttable.bcolors.PURPLE, 'edit', edit))
    for delete in diff.deletes:
      file_rows.append(cls._make_diff_row(texttable.bcolors.RED, 'delete', delete))
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

  @classmethod
  def create(cls, index, theirs, repo=None):
    diff = messages.DiffMessage()
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

    for path, sha in their_paths_to_shas.iteritems():
      file_message = messages.FileMessage()
      file_message.path = path
      file_message.deployed = theirs.deployed
      file_message.deployed_by = theirs.deployed_by
      diff.deletes.append(file_message)

    # What changed in the pod between deploy commits.
    if (repo is not None
        and index.commit and index.commit.sha
        and theirs.commit and theirs.commit.sha):
      try:
        what_changed = repo.git.log(
            '--date=short',
            '--pretty=format:[%h] %ad <%ae> %s',
            '{}..{}'.format(theirs.commit.sha, index.commit.sha)).decode('utf-8')
        diff.what_changed = what_changed
      except git.exc.GitCommandError:
        logging.info('Unable to determine changes between deploys.')

    # If on the original deploy show commit log messages only.
    elif (repo is not None
          and index.commit and index.commit.sha):
      diff.what_changed = repo.git.log(
          '--date=short',
          '--pretty=format:[%h] %ad <%ae> %s').decode('utf-8')

    return diff

  @classmethod
  def to_string(cls, message):
    return protojson.encode_message(message)

  @classmethod
  def apply(cls, message, paths_to_content, write_func, delete_func, threaded=True,
            batch_writes=False):
    # TODO(jeremydw): Thread pool for the threaded operation.
    diff = message
    threads = []
    num_files = len(diff.adds) + len(diff.edits) + len(diff.deletes)
    text = 'Deploying: %(value)d/{} (in %(elapsed)s)'
    widgets = [progressbar.FormatLabel(text.format(num_files))]
    bar = progressbar.ProgressBar(widgets=widgets, maxval=num_files)

    if batch_writes:
      writes_paths_to_contents = {}
      for file_message in diff.adds:
        writes_paths_to_contents[file_message.path] = paths_to_content[file_message.path]
      for file_message in diff.edits:
        writes_paths_to_contents[file_message.path] = paths_to_content[file_message.path]
      deletes_paths = [file_message.path for file_message in diff.deletes]
      if writes_paths_to_contents:
        write_func(writes_paths_to_contents)
      if deletes_paths:
        delete_func(deletes_paths)

    else:
      bar.start()
      for file_message in diff.adds:
        content = paths_to_content[file_message.path]
        thread = ProgressBarThread(
            bar, True, target=write_func, args=(file_message.path, content))
        threads.append(thread)
        thread.start()
        if not threaded:
          thread.join()
      for file_message in diff.edits:
        content = paths_to_content[file_message.path]
        thread = ProgressBarThread(
            bar, True, target=write_func, args=(file_message.path, content))
        threads.append(thread)
        thread.start()
        if not threaded:
          thread.join()
      for file_message in diff.deletes:
        thread = ProgressBarThread(
            bar, batch_writes, target=delete_func, args=(file_message.path,))
        threads.append(thread)
        thread.start()
        if not threaded:
          thread.join()

    if threaded:
      for thread in threads:
        thread.join()
    if not batch_writes:
      bar.finish()


class Index(object):

  @classmethod
  def create(cls, paths_to_contents=None):
    message = messages.IndexMessage()
    message.deployed = datetime.datetime.now()
    message.files = []
    if paths_to_contents is None:
      return message
    for pod_path, contents in paths_to_contents.iteritems():
      cls.add_file(message, pod_path, contents)
    return message

  @classmethod
  def add_file(cls, message, path, contents):
    pod_path = '/' + path.lstrip('/')
    m = hashlib.sha1()
    if isinstance(contents, unicode):
      contents = contents.encode('utf-8')
    m.update(contents)
    sha = m.hexdigest()
    message.files.append(messages.FileMessage(path=pod_path, sha=sha))
    return message

  @classmethod
  def add_repo(cls, message, repo):
    config = repo.config_reader()
    try:
      message.deployed_by = messages.AuthorMessage(
          name=config.get('user', 'name'),
          email=config.get('user', 'email'))
    except ConfigParser.NoSectionError:
      logging.warning("Couldn't find user info in repository config.")
    try:
      commit = repo.head.commit
    except ValueError:
      logging.info('Warning: On initial commit, no HEAD yet.')
      return message
    try:
      repo.git.diff('--quiet')
      has_unstaged_changes = False
    except git.exc.GitCommandError:
      has_unstaged_changes = True
    commit_message = messages.CommitMessage()
    commit_message.has_unstaged_changes = has_unstaged_changes
    commit_message.sha = commit.hexsha
    commit_message.message = commit.message
    commit_message.author = messages.AuthorMessage(
        name=commit.author.name, email=commit.author.email)
    message.commit = commit_message
    return message

  @classmethod
  def to_string(cls, message):
    return protojson.encode_message(message)

  @classmethod
  def from_string(cls, content):
    return protojson.decode_message(messages.IndexMessage, content)
