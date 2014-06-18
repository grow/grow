"""An Env holds the environment context that a pod is running in."""


from protorpc import messages


class Env(object):

  def __init__(self, config):
    self.config = config
    self.host = config.host
    self.port = config.port or 80
    self.scheme = config.scheme or 'http'

  def __repr__(self):
    return '<Env: {}>'.format(self.url)

  @property
  def host(self):
    return self.config.host or 'localhost'

  @host.setter
  def host(self, value):
    self.config.host = value

  @property
  def port(self):
    return self.config.port or 80

  @port.setter
  def port(self, value):
    self.config.port = value

  @property
  def scheme(self):
    return self.config.scheme or 'https'

  @scheme.setter
  def scheme(self, value):
    self.config.scheme = value

  @property
  def url(self):
    url_port = ':{}'.format(self.port)

    # Do not show the port for default ports.
    if ((self.port == 80 and self.scheme == 'http')
        or (self.port == 443 and self.scheme == 'https')):
      url_port = ''

    return '{}://{}{}/'.format(self.scheme, self.host, url_port)

class EnvConfig(messages.Message):
  host = messages.StringField(1)
  scheme = messages.StringField(2)
  port = messages.IntegerField(3)
