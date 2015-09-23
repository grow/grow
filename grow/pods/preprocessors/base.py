import os


class Error(Exception):
  pass


class PreprocessorError(Error):
  pass


class BasePreprocessor(object):

  def __init__(self, pod, config):
    self.pod = pod
    self.root = pod.root
    self.config = config
    self.logger = self.pod.logger

  def first_run(self):
    self.run()

  def run(self):
    raise NotImplementedError

  def list_watched_dirs(self):
    return []

  def normalize_path(self, path):
    if path.startswith('/'):
      return os.path.join(self.root, path.lstrip('/'))
    return path
