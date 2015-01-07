"""An Env holds the environment context that a pod is running in."""

from protorpc import messages


class EnvConfig(messages.Message):
  host = messages.StringField(1)
  scheme = messages.StringField(2)
  port = messages.IntegerField(3)
  name = messages.StringField(4)
  cached = messages.BooleanField(5, default=True)


class Env(object):

  def __init__(self, config):
    self.name = config.name
    self.config = config
    self.host = config.host
    self.port = config.port or 80
    self.scheme = config.scheme or 'http'
    self.cached = config.cached

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

  @classmethod
  def from_wsgi_env(cls, wsgi_env):
    env = cls()
    env.update_from_wsgi_env(wsgi_env)
    return env

  def update_from_wsgi_env(self, wsgi_env):
    self.host = wsgi_env.get('HTTP_HOST', wsgi_env.get('SERVER_NAME', 'localhost'))
    self.scheme = wsgi_env['wsgi.url_scheme']
    self.port = int(wsgi_env.get('SERVER_PORT', 80))

  def to_wsgi_env(self):
    return {
        'REQUEST_METHOD': 'GET',
        'SERVER_NAME': self.host,
        'SERVER_PORT': str(self.port),
        'wsgi.url_scheme': self.scheme,
    }
