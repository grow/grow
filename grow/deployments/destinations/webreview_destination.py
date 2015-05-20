from . import base
from grow.pods import env
from protorpc import messages
import os
import webreview


class Config(messages.Message):
  env = messages.MessageField(env.EnvConfig, 1)
  project = messages.StringField(2, required=True)
  name = messages.StringField(3, required=True)
  server = messages.StringField(4, required=True)
  secure = messages.BooleanField(5, default=True)
  keep_control_dir = messages.BooleanField(6, default=False)


class WebReviewDestination(base.BaseDestination):
  KIND = 'webreview'
  Config = Config
  threaded = True
  batch_writes = True

  def __init__(self, *args, **kwargs):
    super(WebReviewDestination, self).__init__(*args, **kwargs)
    api_key = os.getenv('WEBREVIEW_API_KEY')
    self.webreview = webreview.WebReview(
        project=self.config.project,
        name=self.config.name,
        host=self.config.server,
        secure=self.config.secure,
        api_key=api_key)

  def __str__(self):
    return self.config.server

  def login(self, account='default', reauth=False):
    self.webreview.login(account, reauth=reauth)

  def prelaunch(self, dry_run=False):
    super(WebReviewDestination, self).prelaunch(dry_run=dry_run)

  def test(self):
    # Don't run the default "can write files at destination" test.
    pass

  def read_file(self, path):
    try:
      paths_to_contents, errors = self.webreview.read([path])
      if path not in paths_to_contents:
        raise IOError('{} not found.'.format(path))
      if errors:
        raise base.Error(errors)
      return paths_to_contents[path]
    except webreview.RpcError as e:
      raise base.Error(e.message)

  def write_file(self, paths_to_contents):
    try:
      for path, content in paths_to_contents.iteritems():
        if isinstance(content, unicode):
          paths_to_contents[path] = content.encode('utf-8')
      paths_to_contents, errors = self.webreview.write(paths_to_contents)
      if errors:
        raise base.Error(errors)
      return paths_to_contents
    except webreview.RpcError as e:
      raise base.Error(e.message)

  def delete_file(self, paths):
    try:
      paths_to_contents, errors = self.webreview.delete(paths)
      if errors:
        raise base.Error(errors)
      return paths_to_contents
    except webreview.RpcError as e:
      raise base.Error(e.message)


# Support legacy "jetway" destination. Remove this in a future release.
class LegacyJetwayDestination(WebReviewDestination):
  KIND = 'jetway'
