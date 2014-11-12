from . import base
from grow.pods import env
from grow.pods.storage import storage as storage_lib
from protorpc import messages
import git
import logging
import os
import shutil
import tempfile
import webapp2


class Config(messages.Message):
  env = messages.MessageField(env.EnvConfig, 1)
  repo = messages.StringField(2)
  branch = messages.StringField(3, default='master')
  root_dir = messages.StringField(4, default='')
  keep_control_dir = messages.BooleanField(5, default=False)


class GitDestination(base.BaseDestination):
  KIND = 'git'
  Config = Config
  storage = storage_lib.FileStorage

  def __init__(self, *args, **kwargs):
    super(GitDestination, self).__init__(*args, **kwargs)
    self.adds = set()
    self.deletes = set()
    self._original_branch_name = None

  def __str__(self):
    if self.is_remote:
      prefix = self.config.repo
    else:
      prefix = 'git:{}'.format(self.config.repo)
    return '{}@{}:{}'.format(prefix, self.config.branch, self.config.root_dir)

  @webapp2.cached_property
  def is_remote(self):
    return self.config.repo.startswith(('https://', 'http://', 'git://'))

  @webapp2.cached_property
  def repo_path(self):
    return tempfile.mkdtemp() if self.is_remote else self.config.repo

  @webapp2.cached_property
  def repo(self):
    if self.is_remote:
      return git.Repo.init(self.repo_path)
    return git.Repo(self.repo_path)

  def prelaunch(self, dry_run=False):
    self._original_branch_name = self.repo.active_branch.name
    self.repo.git.checkout(b=self.config.branch)
    if self.is_remote:
      self.remote = git.remote.Remote.add(self.repo, 'origin', self.config.repo)
      try:
        logging.info('Pulling from {}...'.format(self.config.branch))
        self.repo.git.pull('origin', self.config.branch)
      except git.exc.GitCommandError as e:
        # Pass on this error, which will create a new branch upon pushing.
        if "Couldn't find remote ref" not in e.stderr:
          raise

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
    self.repo.index.commit('Commited by Grow SDK.')

    if self.is_remote:
      logging.info('Pushing to origin...')
      self.repo.git.push('origin', self.config.branch)
      shutil.rmtree(self.repo_path)
    elif self._original_branch_name is not None:
      self.repo.git.checkout(b=self._original_branch_name)

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

  def write_file(self, path, content):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    out_path = os.path.join(self.repo_path, self.config.root_dir.lstrip('/'),
                            path.lstrip('/'))
    self.storage.write(out_path, content)
    self.adds.add(out_path)
    if out_path in self.deletes:
      self.deletes.remove(out_path)
