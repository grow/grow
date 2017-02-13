"""Caching for pod meta information."""

from . import documents
from . import dependency
from grow.common import timer


class PodCache(object):

    KEY_DOCUMENTS = 'documents'
    KEY_DEPENDENCIES = 'dependencies'

    def __init__(self, yaml, pod):
        self._pod = pod

        with timer.Timer() as t:
            self._document_cache = documents.DocumentCache(self._pod)
            self._document_cache.add_all(yaml.get(self.KEY_DOCUMENTS, {}))
        print "=> elasped _document_cache: %s s" % t.secs

        with timer.Timer() as t:
            self._dependency_graph = dependency.DependencyGraph()
            self._dependency_graph.add_all(yaml.get(self.KEY_DEPENDENCIES, {}))
        print "=> elasped _dependency_graph: %s s" % t.secs

    @property
    def dependency_graph(self):
        return self._dependency_graph

    @property
    def document_cache(self):
        return self._document_cache

    def reset(self):
        self._dependency_graph.reset()
        self._document_cache.reset()

    def write(self):
        yaml = {}
        yaml[self.KEY_DEPENDENCIES] = self._dependency_graph.export()
        yaml[self.KEY_DOCUMENTS] = self._document_cache.export()
        self._pod.write_yaml('/{}'.format(self._pod.FILE_PODCACHE), yaml)
