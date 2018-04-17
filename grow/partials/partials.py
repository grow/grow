"""Partials contain organized units for templating."""

import re
from grow.partials import partial as grow_partial


class Error(Exception):
    """Generic error base."""
    pass


class Partials(object):
    """Manage partials within the pod."""

    PARTIALS_PATH = '/partials'

    def __init__(self, pod):
        self.pod = pod

    def __repr__(self):
        return '<Partials "{}">'.format(self.PARTIALS_PATH)

    def editor_configs(self):
        """Find all of the editor configs from all partials."""

        for partial in self.get_partials():
            print partial

    def get_partial(self, key):
        """Returns a specific partial in the pod."""
        return grow_partial.Partial('{}/{}'.format(self.PARTIALS_PATH, key), self.pod)

    def get_partials(self):
        """Returns all partials in the pod."""
        items = []
        abs_base_dir = self.pod.abs_path(self.PARTIALS_PATH)
        for root, dirs, _ in self.pod.walk(self.PARTIALS_PATH):
            if root == abs_base_dir:
                for dir_name in dirs:
                    partial = grow_partial.Partial(
                        '{}/{}'.format(self.PARTIALS_PATH, dir_name), self.pod)
                    items.append(partial)
        return items
