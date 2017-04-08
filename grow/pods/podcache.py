"""Caching for pod meta information."""

from . import collection_cache
from . import document_cache
from . import dependency
from grow.common import timer


class PodCache(object):

    KEY_DEPENDENCIES = 'dependencies'

    def __init__(self, yaml, pod):
        self._pod = pod

        self._collection_cache = collection_cache.CollectionCache()
        self._document_cache = document_cache.DocumentCache()

        self._dependency_graph = dependency.DependencyGraph()
        self._dependency_graph.add_all(yaml.get(self.KEY_DEPENDENCIES, {}))

    @property
    def collection_cache(self):
        """Cache for the collections."""
        return self._collection_cache

    @property
    def dependency_graph(self):
        """Dependency graph from rendered docs."""
        return self._dependency_graph

    @property
    def document_cache(self):
        """Cache for specific document properties."""
        return self._document_cache

    def reset(self):
        self._collection_cache.reset()
        self._dependency_graph.reset()
        self._document_cache.reset()

    def write(self):
        yaml = {}
        yaml[self.KEY_DEPENDENCIES] = self._dependency_graph.export()
        self._pod.write_yaml('/{}'.format(self._pod.FILE_PODCACHE), yaml)
