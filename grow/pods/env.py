"""An Env holds the environment context that a pod is running in."""

import time
from protorpc import messages


class Name(object):
    DEV = 'dev'


class EnvConfig(messages.Message):
    host = messages.StringField(1)
    scheme = messages.StringField(2)
    port = messages.IntegerField(3)
    name = messages.StringField(4)
    cached = messages.BooleanField(5, default=True)
    fingerprint = messages.StringField(6)
    dev = messages.BooleanField(7, default=False)


class Env(object):

    def __init__(self, config):
        self.name = config.name
        self.config = config
        self.host = config.host
        self.port = config.port or 80
        self.scheme = config.scheme or 'http'
        self.cached = config.cached
        self.fingerprint = config.fingerprint or str(int(time.time()))

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
    def dev(self):
        return self.config.dev

    @property
    def url(self):
        url_port = ':{}'.format(self.port)
        # Do not show the port for default ports.
        if ((self.port == 80 and self.scheme == 'http')
            or (self.port == 443 and self.scheme == 'https')):
            url_port = ''
        return '{}://{}{}/'.format(self.scheme, self.host, url_port)

    def to_wsgi_env(self):
        return {
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': self.host,
            'SERVER_PORT': str(self.port),
            'wsgi.url_scheme': self.scheme,
        }
