"""An Env holds the environment context that a pod is running in."""

import time
from protorpc import messages
from grow.common import urls


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
        self.config = config
        self.name = config.get('name')
        self.cached = config.get('cached', True)
        self.fingerprint = config.get('fingerprint') or str(int(time.time()))

    def __repr__(self):
        return '<Env: {}>'.format(self.url)

    @property
    def host(self):
        return self.config.get('host', 'localhost')

    @host.setter
    def host(self, value):
        self.config['host'] = value

    @property
    def port(self):
        return self.config.get('port')

    @port.setter
    def port(self, value):
        self.config['port'] = value

    @property
    def scheme(self):
        return self.config.get('scheme')

    @scheme.setter
    def scheme(self, value):
        self.config['scheme'] = value

    @property
    def dev(self):
        return self.config.get('dev', False)

    @property
    def url(self):
        return urls.Url(
            path='/',
            host=self.host,
            port=self.port,
            scheme=self.scheme)

    def to_wsgi_env(self):
        return {
            'REQUEST_METHOD': 'GET',
            'SERVER_NAME': self.host,
            'SERVER_PORT': str(self.port),
            'wsgi.url_scheme': self.scheme,
        }
