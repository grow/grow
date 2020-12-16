"""Partials contain organized units for templating."""

import os
from grow.partials import partial as grow_partial


class Partials(object):
    """Manage partials within the pod."""

    PARTIALS_PATH = '/partials'
    VIEWS_PATH = '/views/partials'

    def __init__(self, pod):
        self.pod = pod

    def __repr__(self):
        return '<Partials "{}">'.format(self.PARTIALS_PATH)

    def get_partial(self, key):
        """Returns a specific partial in the pod."""
        # Check if the partial is a view partial.
        pod_path = '{}/{}.html'.format(self.VIEWS_PATH, key)
        if self.pod.file_exists(pod_path):
            return grow_partial.ViewPartial(pod_path, self.pod)

        pod_path = '{}/{}'.format(self.PARTIALS_PATH, key)
        return grow_partial.Partial(pod_path, self.pod)

    def get_partials(self):
        """Returns all partials in the pod."""
        items = []

        # Load all partials in the partials directory.
        abs_base_dir = self.pod.abs_path(self.PARTIALS_PATH)
        for root, dirs, _ in self.pod.walk(self.PARTIALS_PATH):
            if root == abs_base_dir:
                for dir_name in dirs:
                    pod_path = '{}/{}'.format(self.PARTIALS_PATH, dir_name)
                    partial = grow_partial.Partial(pod_path, self.pod)
                    items.append(partial)

        # Load all partials in the views partials directory.
        view_pod_paths = []
        for root, dirs, files in self.pod.walk(self.VIEWS_PATH):
            pod_dir = root.replace(self.pod.root, '')
            for file_name in files:
                pod_path = os.path.join(pod_dir, file_name)
                partial = grow_partial.ViewPartial(pod_path, self.pod)
                items.append(partial)

        return items
