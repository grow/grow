"""Partials contain organized units for templating."""

import os
from grow.documents import document_front_matter
from grow.common import utils


split_front_matter = document_front_matter.DocumentFrontMatter.split_front_matter


class Partial(object):
    """Partial from the partial directory."""

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
    def config(self):
        if not self.exists:
            return {}

        front_matter, _ = split_front_matter(
            self.pod.read_file(self.template_pod_path))
        if not front_matter:
            return {}
        return utils.parse_yaml(front_matter, pod=self.pod)

    @property
    def exists(self):
        return self.pod.file_exists(self.pod_path)

    @property
    def template_pod_path(self):
        return os.path.join(self.pod_path, '{}.html'.format(self.key))


class ViewPartial(object):
    """Partial from the views directory."""

    def __init__(self, pod_path, pod):
        self.pod_path = self.clean_path(pod_path)
        base, _ = os.path.splitext(self.pod_path)
        self.key = os.path.basename(base)
        self.pod = pod

    def __repr__(self):
        return '<ViewPartial "{}">'.format(self.key)

    @classmethod
    def clean_path(cls, pod_path):
        """Clean up the pod path for the partial."""
        return pod_path

    @property
    def config(self):
        if not self.exists:
            return {}

        front_matter, _ = split_front_matter(self.pod.read_file(
            self.template_pod_path))
        if not front_matter:
            return {}
        return utils.parse_yaml(front_matter, pod=self.pod)

    @property
    def exists(self):
        return self.pod.file_exists(self.pod_path)

    @property
    def template_pod_path(self):
        return self.pod_path
