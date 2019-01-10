"""URL utility class."""

import os


class Url(object):
    """Url utility class."""

    def __init__(self, path, host=None, port=None, scheme=None):
        self.path = path
        self.host = 'localhost' if host is None else host
        self.scheme = 'http' if scheme is None else scheme
        default_port = 80
        if self.scheme == 'https':
            default_port = 443
        self.port = default_port if port is None else port
        if scheme is None and self.port == 443:
            self.scheme = 'https'

    def __str__(self):
        url = '{}://{}'.format(self.scheme, self.host)
        if ((self.scheme == 'http' and self.port != 80)
                or (self.scheme == 'https' and self.port != 443)):
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
    def create_relative_path(path, relative_to):
        """Create a relative path to another url."""
        if isinstance(path, Url):
            path = path.path
        if path.startswith(('http://', 'https://')):
            return path

        # Need to support relative paths that are not directories.
        if not path.endswith('/') or not relative_to.endswith('/'):
            if path.endswith('/'):
                path_head = path
                path_tail = None
            else:
                path_head, path_tail = os.path.split(path)

            if relative_to.endswith('/'):
                relative_head = relative_to
            else:
                relative_head, _ = os.path.split(relative_to)

            result = os.path.relpath(path_head, relative_head)
            if path_tail:
                result = '{}/{}'.format(result, path_tail)
        else:
            result = os.path.relpath(path, relative_to)
        if path.endswith('/'):
            result = result + '/'
        if not result.startswith(('/', '.')):
            return './' + result
        return result
