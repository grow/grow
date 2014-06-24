import logging
import os



class BasePreprocessor(object):

  def __init__(self, root, config):
    self.root = root
    self.config = config
    self.logger = logging.getLogger('preprocessor')

  def first_run(self):
    self.run()

  def run(self):
    raise NotImplementedError

  def list_watched_dirs(self):
    return []

  def normalize_path(self, path):
    return os.path.join(self.root, path.lstrip('/'))
