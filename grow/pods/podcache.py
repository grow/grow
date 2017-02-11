"""Caching for pod meta information."""

from . import documents
from . import dependency


class PodCache(object):

    KEY_DOCUMENTS = 'documents'
    KEY_DEPENDENCIES = 'dependencies'

    def __init__(self, yaml, pod):
        self._pod = pod
        self._document_cache = documents.DocumentCache(self._pod)
        self._dependency_graph = dependency.DependencyGraph()
        self._dependency_graph.add_all(yaml.get(self.KEY_DEPENDENCIES, {}))

    @property
    def dependency_graph(self):
        return self._dependency_graph

    @property
    def document_cache(self):
        return self._document_cache

    def write(self):
        yaml = {}
        yaml[self.KEY_DEPENDENCIES] = self._dependency_graph.export()
        yaml[self.KEY_DOCUMENTS] = self._dependency_graph.export()

        self._pod.write_yaml('/{}'.format(self._pod.FILE_PODCACHE), yaml)
