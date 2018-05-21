"""Partials contain organized units for templating."""

import os
import re
import yaml


class Partial(object):
    EDITOR_PATH = '_editor.yaml'
    IGNORE_INITIAL = ('_',)
    PARTIALS_PATH = '/partials'

    def __init__(self, pod_path, pod):
        self.pod_path = self.clean_path(pod_path)
        self.key = os.path.basename(self.pod_path)
        self.pod = pod

    def __repr__(self):
        return '<Partial "{}">'.format(self.key)

    @classmethod
    def clean_path(cls, pod_path):
        """Clean up the pod path for the partials."""
        return pod_path.rstrip('/')

    @property
    def editor_config(self):
        """Return the editor configuration for the partial."""
        editor_path = '{}/{}'.format(self.pod_path, self.EDITOR_PATH)
        if self.pod.file_exists(editor_path):
            raw_yaml = self.pod.read_file(editor_path)
            return yaml.load(raw_yaml)
        return {}

    @property
    def exists(self):
        return self.pod.file_exists(self.pod_path)
