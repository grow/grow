class BasePreprocessor(object):

  def __init__(self, pod):
    self.pod = pod

  def set_params(self, **kwargs):
    pass

  def first_run(self):
    self.run()

  def run(self):
    raise NotImplementedError

  def list_watched_dirs(self):
    return []
