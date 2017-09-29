"""Caching for pod meta information."""

import json
from grow.cache import collection_cache
from grow.cache import document_cache
from grow.cache import file_cache
from grow.cache import object_cache
from grow.pods import dependency


class Error(Exception):
    """General podcache error."""
    pass


class PodCacheParseError(Error):
    """Error parsing the podcache file."""
    pass


class PodCache(object):
    """Caching container for the pod."""

    KEY_GLOBAL = '__global__'

    def __init__(self, dep_cache, obj_cache, pod):
        self._pod = pod

        self._collection_cache = collection_cache.CollectionCache()
        self._document_cache = document_cache.DocumentCache()
        self._file_cache = file_cache.FileCache()

        self._dependency_graph = dependency.DependencyGraph()
        self._dependency_graph.add_all(dep_cache)

        self._object_caches = {}
        self.create_object_cache(
            self.KEY_GLOBAL, write_to_file=False, can_reset=True)

        existing_object_caches = obj_cache
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
    def file_cache(self):
        """Cache for raw file contents."""
        return self._file_cache

    @property
    def is_dirty(self):
        """Have the contents of the dependency graph or caches been modified?"""
        if self.dependency_graph.is_dirty:
            return True
        for meta in self._object_caches.itervalues():
            if meta['write_to_file'] and meta['cache'].is_dirty:
                return True
        return False

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
        self._file_cache.reset()

        # Only reset the object caches if permitted.
        for meta in self._object_caches.itervalues():
            if meta['can_reset'] or force:
                meta['cache'].reset()

    def update(self, dep_cache=None, obj_cache=None):
        if dep_cache:
            self._dependency_graph.add_all(dep_cache)

        if obj_cache:
            for key, meta in obj_cache.iteritems():
                if not key in self._object_caches:
                    self.create_object_cache(key, **meta)
                else:
                    self._object_caches[key]['cache'].add_all(meta['values'])
                    self._object_caches[key]['write_to_file'] = meta['write_to_file']
                    self._object_caches[key]['can_reset'] = meta['can_reset']

    def write(self):
        """Persist the cache information to a yaml file."""
        with self._pod.profile.timer('podcache.write'):
            if self._dependency_graph.is_dirty:
                output = self._dependency_graph.export()
                self._dependency_graph.mark_clean()
                self._pod.write_file(
                    '/{}'.format(self._pod.FILE_DEP_CACHE),
                    json.dumps(output, sort_keys=True, indent=2, separators=(',', ': ')))

            # Write out any of the object caches configured for write_to_file.
            output = {}
            for key, meta in self._object_caches.iteritems():
                if meta['write_to_file']:
                    output[key] = {
                        'can_reset': meta['can_reset'],
                        'write_to_file': meta['write_to_file'],
                        'values': meta['cache'].export(),
                    }
                    meta['cache'].mark_clean()
            if output:
                self._pod.write_file(
                    '/{}'.format(self._pod.FILE_OBJECT_CACHE),
                    json.dumps(output, sort_keys=True, indent=2, separators=(',', ': ')))
