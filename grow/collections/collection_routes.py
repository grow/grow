"""Routing information for the collection."""

import os
import yaml
from grow.common import untag


class CollectionRoutes(object):
    """Collection level routing information."""

    ROUTES_PATH = '_routes.yaml'

    def __init__(self, pod, collection_path):
        self.pod = pod
        self.collection_path = collection_path
        self.routes_path = os.path.join(collection_path, self.ROUTES_PATH)
        self.pod_paths = {}
        self._read_routes()

    def _get_meta(self, pod_path):
        return self.pod_paths.get(pod_path, {})

    def _read_routes(self):
        if not self.pod.file_exists(self.routes_path):
            return

        # The utils parsing causes recursion errors, so needs to be normal yaml.
        raw_routes = yaml.load(self.pod.read_file(self.routes_path))
        # Untag to get the right values for the environment.
        routes = untag.Untag.untag(
            raw_routes, params={
                'env': untag.UntagParamRegex(self.pod.env.name),
            })
        self.pod_paths = routes['pod_paths']

    def localization(self, pod_path, default_value=None):
        """Get document localization information."""
        data = self._get_meta(pod_path)
        return data.get('localization', default_value)

    def path(self, pod_path, default_value=None):
        """Get document base serving path."""
        data = self._get_meta(pod_path)
        return data.get('path', default_value)
