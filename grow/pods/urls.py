import os


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

    def __eq__(self, other):
        return (
            isinstance(other, Url)
            and self.path == other.path
            and self.host == other.host
            and self.port == other.port
            and self.scheme == other.scheme)

    def __repr__(self):
        return '<Url: {}>'.format(str(self))

    def __cmp__(self, other):
        return cmp(self.path, other.path)

    @staticmethod
    def format_path(path, pod):
        pass

    @staticmethod
    def create_relative_path(path, relative_to):
        if isinstance(path, Url):
            path = path.path
        if path.startswith(('http://', 'https://')):
            return path
        result = os.path.relpath(path, relative_to)
        if path.endswith('/'):
          result = result + '/'
        if not result.startswith(('/', '.')):
          return './' + result
        return result
