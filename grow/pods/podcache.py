"""Caching for pod meta information."""

from . import collection_cache
from . import document_cache
from . import dependency
from . import object_cache


class Error(Exception):
    """General podcache error."""
    pass


class PodCacheParseError(Error):
    """Error parsing the podcache file."""
    pass


class PodCache(object):
    """Caching container for the pod."""

    KEY_DEPENDENCIES = 'dependencies'
    KEY_GLOBAL = '__global__'
    KEY_OBJECTS = 'objects'

    def __init__(self, yaml, pod):
        self._pod = pod

        self._collection_cache = collection_cache.CollectionCache()
        self._document_cache = document_cache.DocumentCache()

        self._dependency_graph = dependency.DependencyGraph()
        self._dependency_graph.add_all(yaml.get(self.KEY_DEPENDENCIES, {}))

        self._object_caches = {}
        self.create_object_cache(
            self.KEY_GLOBAL, write_to_file=False, can_reset=True)

        existing_object_caches = yaml.get(self.KEY_OBJECTS, {})
        for key, item in existing_object_caches.iteritems():
            self.create_object_cache(key, **item)

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

    @property
    def object_cache(self):
        """Global object cache."""
        return self.get_object_cache(self.KEY_GLOBAL)

    def create_object_cache(self, key, write_to_file=False, can_reset=False, values=None):
        """Create a named object cache."""
        self._object_caches[key] = {
            'cache': object_cache.ObjectCache(),
            'write_to_file': write_to_file,
            'can_reset': can_reset,
        }
        cache = self._object_caches[key]['cache']
        if values:
            cache.add_all(values)

        return cache

    def get_object_cache(self, key, **kwargs):
        """Get an existing object cache or create a new cache with defaults."""
        if key not in self._object_caches:
            return self.create_object_cache(key, **kwargs)
        return self._object_caches[key]['cache']

    def has_object_cache(self, key):
        """Has an existing object cache?"""
        return key in self._object_caches

    def reset(self, force=False):
        """Reset pod caches."""
        self._collection_cache.reset()
        self._dependency_graph.reset()
        self._document_cache.reset()

        # Only reset the object caches if permitted.
        for meta in self._object_caches.itervalues():
            if meta['can_reset'] or force:
                meta['cache'].reset()

    def write(self):
        """Persist the cache information to a yaml file."""
        yaml = {}
        yaml[self.KEY_DEPENDENCIES] = self._dependency_graph.export()
        yaml[self.KEY_OBJECTS] = {}

        self._dependency_graph.mark_clean()

        # Write out any of the object caches that request to be exported to
        # file.
        for key, meta in self._object_caches.iteritems():
            if meta['write_to_file']:
                yaml[self.KEY_OBJECTS][key] = {
                    'can_reset': meta['can_reset'],
                    'write_to_file': meta['write_to_file'],
                    'values': meta['cache'].export(),
                }

        self._pod.write_yaml('/{}'.format(self._pod.FILE_PODCACHE), yaml)
