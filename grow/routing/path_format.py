"""Path formatter for formatting grow paths."""

class PathFormat(object):
    """Format url paths using the information from the pod."""

    def __init__(self, pod):
        self.pod = pod

    @staticmethod
    def strip_double_slash(path):
        """Remove double slashes from the path."""
        while '//' in path:
            path = path.replace('//', '/')
        return path

    def format_pod(self, path):
        """Format a URL path using the pod information."""
        path = '' if path is None else path
        if 'root' in self.pod.podspec:
            path = path.replace('{root}', self.pod.podspec['root'])
        if self.pod.env.fingerprint:
            path = path.replace('{env.fingerprint}', self.pod.env.fingerprint)
        return PathFormat.strip_double_slash(path)
