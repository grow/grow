"""Routing information for the collection."""

import os


class CollectionRoutes(object):
    """Collection level routing information."""

    ROUTES_PATH = '_routes.yaml'

    def __getattr__(self, attr):
        def _get_field(pod_path, default_value=None):
            return self.get_field(pod_path, attr, default_value)
        return _get_field

    def __init__(self, pod_paths=None):
        self.pod_paths = pod_paths or {}

    def _get_meta(self, pod_path):
        pod_path = pod_path.lstrip(os.path.sep)
        return self.pod_paths.get(pod_path, {})

    def get_field(self, pod_path, field, default_value=None):
        """Get document field from metadata."""
        data = self._get_meta(pod_path)
        return data.get(field, default_value)
