"""Grow static document."""

import hashlib
import os
from grow.common import urls
from grow.routing import path_filter as grow_path_filter


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

        # When localized the base string is changed.
        self.base_source_path = self.config['static_dir']

        self.use_locale = locale is not None and locale != pod.podspec.default_locale
        if self.use_locale and 'localization' in self.config:
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
        return self.pod.file_exists(self.source_pod_path)

    @property
    def filter(self):
        """Static configuration filter."""
        return self.config.get('filter', {})

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
    def fingerprinted(self):
        """Fingerprint file contents?"""
        return self.config.get('fingerprinted', False)

    @property
    def path_filter(self):
        """Path filter for the static document."""
        static_filter = self.filter
        if static_filter:
            return grow_path_filter.PathFilter(
                static_filter.get('ignore_paths'), static_filter.get('include_paths'))
        return self.pod.path_filter

    @property
    def path_format(self):
        """Path format for the static document."""
        return '{}{}'.format(
            self.config['serve_at'],
            self.sub_base_pod_path)

    @property
    def source_format(self):
        """Path format for the source of the document."""
        return '{}{}'.format(
            self.source_path,
            self.sub_base_pod_path)

    @property
    def serving_path(self):
        """Serving path for the static document."""
        path = self.pod.path_format.format_static(
            self.path_format, locale=self.locale)

        if not self.fingerprinted:
            return path

        base, ext = os.path.splitext(path)
        # Special case to preserve ".min.<ext>" extensions.
        if base.endswith('.min'):
            base = base[:-4]
            return '{}-{}.min{}'.format(base, self.fingerprint, ext)
        return '{}-{}{}'.format(base, self.fingerprint, ext)

    @property
    def serving_path_parameterized(self):
        """Parameterized serving path for the static document."""
        return self.pod.path_format.format_static(
            self.path_format, locale=self.locale, parameterize=True)

    @property
    def source_path(self):
        """Source path for the static document."""
        return self.config['static_dir']

    @property
    def source_pod_path(self):
        """Source path for the static document with missing file fallback."""
        source_path = self.pod.path_format.format_static(
            self.source_format, locale=self.locale)
        # Fall back to the pod path if using locale and the localized
        # version does not exist.
        if not self.pod.file_exists(source_path) and self.use_locale:
            source_path = self.pod_path
        return source_path

    @property
    def sub_base_pod_path(self):
        """Unique portion of the base static file."""
        return self.pod_path[len(self.base_source_path):]

    @property
    def sub_pod_path(self):
        """Unique portion of the full static file."""
        return self.pod_path[len(self.source_path):]

    @property
    def url(self):
        """URL of the file contents."""
        return urls.Url(
            path=self.serving_path,
            host=self.pod.env.host,
            port=self.pod.env.port,
            scheme=self.pod.env.scheme)
