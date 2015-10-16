class Url(object):

  def __init__(self, path, host=None, port=None, scheme=None):
    self.path = path
    self.host = 'localhost' if host is None else host
    self.port = 80 if port is None else port
    self.scheme = 'http' if scheme is None else scheme

  def __str__(self):
    url = '{}://{}'.format(self.scheme, self.host)
    if self.port != 80:
      url += ':{}'.format(self.port)
    url += self.path
    return url

  def __repr__(self):
    return '<Url: {}>'.format(str(self))

  @staticmethod
  def format_path(path, pod):
    pass
