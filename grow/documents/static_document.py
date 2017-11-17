"""Grow static document."""

import hashlib
from grow.common import urls


class Error(Exception):
    """Base rendering pool error."""
    pass


class StaticDocument(object):
    """Static document."""

    def __eq__(self, other):
        return (self.pod == other.pod and self.pod_path == other.pod_path
                and other.locale == self.locale)

    def __init__(self, pod, pod_path, locale=None):
        self.pod = pod
        self.pod_path = pod_path
        self.locale = locale
        self.config = self.pod.router.get_static_config_for_pod_path(pod_path)
        if self.locale is not None and 'localization' in self.config:
            inherited = {
                'fingerprinted': self.config.get('fingerprinted', False),
            }
            self.config = self.config.get('localization')
            self.config.update(inherited)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        if self.locale:
            return "<StaticDocument({}, locale='{}')>".format(
                self.pod_path, self.locale)
        return "<StaticDocument({})>".format(self.pod_path)

    def _create_fingerprint(self):
        with self.pod.open_file(self.pod_path, 'rb') as pod_file:
            return hashlib.md5(pod_file.read()).hexdigest()

    @property
    def exists(self):
        """Does the static file exist in the pod?"""
        return self.pod.file_exists(self.pod_path)

    @property
    def modified(self):
        """File modified timestamp."""
        return self.pod.file_modified(self.pod_path)

    @property
    def size(self):
        """Static file size."""
        return self.pod.file_size(self.pod_path)

    @property
    def fingerprint(self):
        """Fingerprint of the file contents."""
        return self._create_fingerprint()

    @property
    def path_format(self):
        """Path format for the static document."""
        return '{}{}'.format(
            self.config['serve_at'],
            self.sub_pod_path)

    @property
    def serving_path(self):
        """Serving path for the static document."""
        return self.pod.path_format.format_static(self)

    @property
    def serving_path_parameterized(self):
        """Parameterized serving path for the static document."""
        return self.pod.path_format.format_static(self, parameterize=True)

    @property
    def source_path(self):
        """Source path for the static document."""
        return self.config['static_dir']

    @property
    def sub_pod_path(self):
        """Unique portion of the static file."""
        return self.pod_path[len(self.source_path):]

    @property
    def url(self):
        """URL of the file contents."""
        return urls.Url(
            path=self.serving_path,
            host=self.pod.env.host,
            port=self.pod.env.port,
            scheme=self.pod.env.scheme)
