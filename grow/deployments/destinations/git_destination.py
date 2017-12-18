"""Git deploy destination."""

import logging
import os
import re
import shutil
import subprocess
import tempfile
from grow.common import utils as common_utils
from grow.pods import env
from grow.storage import file_storage
from protorpc import messages
from . import base


ONLINE_REPO_REGEX = \
    r'((git|ssh|http(s)?)|(git@[\w\.]+))(:(//)?)([\w\.@\:/\-~]+)(\.git)(/)?'


class Config(messages.Message):
    env = messages.MessageField(env.EnvConfig, 1)
    repo = messages.StringField(2)
    branch = messages.StringField(3, default='master')
    root_dir = messages.StringField(4, default='')
    keep_control_dir = messages.BooleanField(5, default=False)


class GitDestination(base.BaseDestination):
    """Git deploy destination."""
    KIND = 'git'
    Config = Config
    storage = file_storage.FileStorage

    def __init__(self, *args, **kwargs):
        super(GitDestination, self).__init__(*args, **kwargs)
        self.adds = set()
        self.deletes = set()
        self._original_branch_name = None
        self._git = common_utils.get_git()

    def __str__(self):
        if self.is_remote:
            prefix = self.config.repo
        else:
            prefix = 'git:{}'.format(self.config.repo)
        return '{}@{}:{}'.format(prefix, self.config.branch, self.config.root_dir)

    @common_utils.cached_property
    def is_remote(self):
        return re.match(ONLINE_REPO_REGEX, self.config.repo)

    @common_utils.cached_property
    def repo_path(self):
        if self.is_remote:
            return tempfile.mkdtemp()
        else:
            return os.path.abspath(self.config.repo)

    @common_utils.cached_property
    def repo(self):
        if self.is_remote:
            return self._git.Repo.init(self.repo_path)
        return self._git.Repo(self.repo_path)

    def _checkout(self, branch=None):
        branch = branch or self.config.branch
        try:
            self.repo.git.checkout(b=branch)
        except self._git.GitCommandError as e:
            if e.status == 128:
                self.repo.git.checkout(branch)

    def prelaunch(self, dry_run=False):
        self._original_branch_name = self.repo.active_branch.name
        self._checkout()
        if self.is_remote:
            self.remote = self._git.remote.Remote.add(self.repo, 'origin', self.config.repo)
            try:
                logging.info('Pulling from {}...'.format(self.config.branch))
                self.repo.git.pull('origin', self.config.branch)
            except self._git.GitCommandError as e:
                # Pass on this error, which will create a new branch upon pushing.
                if "Couldn't find remote ref" not in e.stderr:
                    raise

    def create_commit_message(self):
        editor = os.getenv('EDITOR')
        commit_message_path = os.path.join(self.repo.git_dir, 'COMMIT_EDITMSG')
        fp = open(commit_message_path, 'w')
        fp.write(self._diff.what_changed or '')
        fp.close()
        if editor and self._confirm:
            subprocess.call('{} {}', editor, commit_message_path, shell=True)
        content = open(commit_message_path).read()
        return content

    def postlaunch(self, dry_run=False):
        if dry_run:
            if self.is_remote:
                shutil.rmtree(self.repo_path)
            return

        if self.adds:
            self.repo.index.add(self.adds)
        if self.deletes:
            self.repo.index.remove(self.deletes)

        if not self.adds and not self.deletes:
            logging.info('No changes, aborting.')
            return

        # TODO: Replace with a user-configurable launch message.
        self.repo.index.commit(self.create_commit_message())

        if self.is_remote:
            logging.info('Pushing to origin...')
            self.repo.git.push('origin', self.config.branch)
            shutil.rmtree(self.repo_path)
        elif self._original_branch_name is not None:
            self._checkout(self._original_branch_name)

    def read_file(self, path):
        path = os.path.join(self.repo_path, self.config.root_dir.lstrip('/'),
                            path.lstrip('/'))
        return self.storage.read(path)

    def delete_control_file(self, path):
        path = os.path.join(self.control_dir, path.lstrip('/'))
        out_path = self.delete_file(path)
        # Control files should remain in the index, for now.
        self.deletes.remove(out_path)

    def delete_file(self, path):
        out_path = os.path.join(self.repo_path, self.config.root_dir.lstrip('/'),
                                path.lstrip('/'))
        self.storage.delete(out_path)
        self.deletes.add(out_path)
        if out_path in self.adds:
            self.adds.remove(out_path)
        return out_path

    def write_file(self, rendered_doc):
        path = rendered_doc.path
        content = rendered_doc.read()
        out_path = os.path.join(self.repo_path, self.config.root_dir.lstrip('/'),
                                path.lstrip('/'))
        self.storage.write(out_path, content)
        self.adds.add(out_path)
        if out_path in self.deletes:
            self.deletes.remove(out_path)
