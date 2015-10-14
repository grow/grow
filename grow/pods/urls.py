class Url(object):

  def __init__(self, path, host=None, port=None, scheme=None):
    self.path = path
    self.host = host
    self.port = port
    self.scheme = scheme

  @staticmethod
  def format_path(path, pod):
    pass
