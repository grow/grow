from . import dependency


class Error(Exception):
    pass


class PodCacheParseError(Error):
    pass


class PodCache(object):

    KEY_DEPENDENCIES = 'dependencies'

    def __init__(self, yaml, pod):
        self._pod = pod
        self._dependency_graph = dependency.DependencyGraph()
        self._dependency_graph.add_all(yaml.get(self.KEY_DEPENDENCIES, {}))

    @property
    def dependency_graph(self):
        return self._dependency_graph

    def write(self):
        yaml = {}
        yaml[self.KEY_DEPENDENCIES] = self._dependency_graph.export()

        self._pod.write_yaml('/{}'.format(self._pod.FILE_PODCACHE), yaml)
