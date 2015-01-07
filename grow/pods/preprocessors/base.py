import logging
import os

_handler = logging.StreamHandler()
_handler.setFormatter(logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S'))
_logger = logging.getLogger('preprocessor')
_logger.propagate = False
_logger.addHandler(_handler)


class Error(Exception):
  pass


class PreprocessorError(Error):
  pass


class BasePreprocessor(object):

  def __init__(self, pod, config):
    self.pod = pod
    self.root = pod.root
    self.config = config
    self.logger = _logger

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
