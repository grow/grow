from . import base
from protorpc import messages
from grow.pods import env
from grow.pods.storage import storage as storage_lib
import os


class Config(messages.Message):
  out_dir = messages.StringField(1, default='')
  env = messages.MessageField(env.EnvConfig, 2)
  keep_control_dir = messages.BooleanField(3, default=False)
  before_deploy = messages.StringField(4, repeated=True)
  after_deploy = messages.StringField(5, repeated=True)


class LocalDestination(base.BaseDestination):
  KIND = 'local'
  Config = Config
  storage = storage_lib.FileStorage

  def __str__(self):
    return 'file://{}'.format(self.config.out_dir)

  def read_file(self, path, buildsuffix=''):
    path = os.path.join(self.config.out_dir, path.lstrip('/'))
    return self.storage.read(path)

  def delete_file(self, path, buildsuffix=''):
    out_path = os.path.join(self.config.out_dir, path.lstrip('/'))
    self.storage.delete(out_path)

  def write_file(self, path, content, buildsuffix=''):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    out_path = os.path.join(self.config.out_dir, path.lstrip('/'))
    self.storage.write(out_path, content)

  def prelaunch(self, dry_run=False):
    for command in self.config.before_deploy:
      self.command(command)
    super(LocalDestination, self).prelaunch(dry_run)

  def postlaunch(self, dry_run=False):
    if self._success:
      for command in self.config.after_deploy:
        self.command(command)
    super(LocalDestination, self).postlaunch(dry_run)
