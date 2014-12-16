from . import base
from grow.pods import env
from protorpc import messages
import jetway



class Config(messages.Message):
  env = messages.MessageField(env.EnvConfig, 1)
  project = messages.StringField(2, required=True)
  name = messages.StringField(3, required=True)
  server = messages.StringField(4, required=True)
  is_secure = messages.BooleanField(5, default=True)
  keep_control_dir = messages.BooleanField(6, default=False)


class JetwayDestination(base.BaseDestination):
  KIND = 'jetway'
  Config = Config

  def __init__(self, *args, **kwargs):
    super(JetwayDestination, self).__init__(*args, **kwargs)
    self.jetway = jetway.Jetway(
        project=self.config.project,
        name=self.config.name,
        host=self.config.server,
        secure=self.config.is_secure)

  def __str__(self):
    return self.config.server

  def prelaunch(self, dry_run=False):
    pass

  def postlaunch(self, dry_run=False):
    pass

  def read_file(self, path):
    paths_to_contents, errors = self.jetway.read([path])
    if errors:
      raise base.Error(errors)
    if path not in paths_to_contents:
      raise IOError('{} not found.'.format(path))
    return paths_to_contents[path]

  def write_file(self, path, content):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    paths_to_contents, errors = self.jetway.write({path: content})
    if errors:
      raise base.Error(errors)
    return paths_to_contents[path]

  def delete_file(self, path):
    paths_to_contents, errors = self.jetway.delete([path])
    if errors:
      raise base.Error(errors)
    return paths_to_contents[path]
