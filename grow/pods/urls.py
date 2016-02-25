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

    @property
    def relative_path(self):
        if self.relative_to is None:
            return self.path
        path = self.relative_to
        num_slashes = path.count('/')
        if num_slashes == 1:
          return './'
        parts = ''.join(['../' for _ in range(path.count('/'))[1:]])
        return parts + self.path[1:]
