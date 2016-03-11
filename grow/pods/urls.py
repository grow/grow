import os


class Url(object):

    def __init__(self, path, host=None, port=None, scheme=None, relative_to=None):
        self.path = path
        self.host = 'localhost' if host is None else host
        self.port = 80 if port is None else port
        self.scheme = 'http' if scheme is None else scheme
        self.relative_to = relative_to

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

    @staticmethod
    def create_relative_path(path, relative_to):
        result = os.path.relpath(path, relative_to)
        if path.endswith('/'):
          result = result + '/'
        if not result.startswith(('/', '.')):
          return './' + result
