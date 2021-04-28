"""Caching for pod meta information."""

import json
import os
import tempfile
from grow.cache import collection_cache
from grow.cache import document_cache
from grow.cache import file_cache
from grow.cache import object_cache
from grow.cache import routes_cache as grow_routes_cache
from grow.common import json_encoder
from grow.pods import dependency


FILE_OBJECT_CACHE = object_cache.FILE_OBJECT_CACHE
FILE_ROUTES_CACHE = grow_routes_cache.FILE_ROUTES_CACHE


class Error(Exception):
    """General podcache error."""

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class PodCacheParseError(Error):
    """Error parsing the podcache file."""
    pass


class PodCache(object):
    """Caching container for the pod."""

    KEY_GLOBAL = '__global__'

    def __init__(self, dep_cache, obj_cache, routes_cache, pod):
        self._pod = pod

        self._collection_cache = collection_cache.CollectionCache()
        self._document_cache = document_cache.DocumentCache()
        self._file_cache = file_cache.FileCache()

        self._dependency_graph = dependency.DependencyGraph()
        self._dependency_graph.add_all(dep_cache)

        self._object_caches = {}
        self.create_object_cache(
            self.KEY_GLOBAL, write_to_file=False, can_reset=True)

        for key, item in obj_cache.items():
            # If this is a string, it is written to a separate cache file.
            if isinstance(item, str):
                cache_value = {}
                if self._pod.file_exists(item):
                    cache_value = self._pod.read_json(item)
                self.create_object_cache(key, **cache_value)
            else:
                self.create_object_cache(key, **item)

        self._routes_cache = grow_routes_cache.RoutesCache()
        self._routes_cache.from_data(routes_cache)

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
        for meta in self._object_caches.values():
            if meta['write_to_file'] and meta['cache'].is_dirty:
                return True
        if self.routes_cache.is_dirty:
            return True
        return False

    @property
    def object_cache(self):
        """Global object cache."""
        return self.get_object_cache(self.KEY_GLOBAL)

    @property
    def routes_cache(self):
        """Global routes cache."""
        return self._routes_cache

    def _write_json(self, path, obj):
        output = json.dumps(
            obj, cls=json_encoder.GrowJSONEncoder,
            sort_keys=True, indent=2, separators=(',', ': '))
        temp_dir = self._pod.abs_path('/.grow/tmp')
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir)
        fd, temp_path = tempfile.mkstemp(dir=temp_dir)
        with os.fdopen(fd, 'w') as fp:
            fp.write(output)
        real_path = self._pod.abs_path(path)
        dir_name = os.path.dirname(real_path)
        if not os.path.exists(dir_name):
            os.makedirs(dir_name)
        os.rename(temp_path, real_path)

    def create_object_cache(self, key, write_to_file=False, can_reset=False, values=None,
                            separate_file=False):
        """Create a named object cache."""
        self._object_caches[key] = {
            'cache': object_cache.ObjectCache(),
            'write_to_file': write_to_file,
            'can_reset': can_reset,
            'separate_file': separate_file,
        }
        cache = self._object_caches[key]['cache']
        if values:
            cache.add_all(values)
        return cache

    def get_object_cache(self, key, **kwargs):
        """Get an existing object cache or create a new cache with defaults."""
        if key not in self._object_caches:
            return self.create_object_cache(key, **kwargs)
        existing_meta = self._object_caches[key]
        if 'separate_file' in kwargs:
            if existing_meta['separate_file'] != kwargs['separate_file']:
                existing_meta['separate_file'] = kwargs['separate_file']
        return existing_meta['cache']

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
        for meta in self._object_caches.values():
            if meta['can_reset'] or force:
                meta['cache'].reset()

    def update(self, dep_cache=None, obj_cache=None):
        """Update the values in the dependency cache and/or the object cache."""
        if dep_cache:
            self._dependency_graph.add_all(dep_cache)

        if obj_cache:
            for key, meta in obj_cache.items():
                if not key in self._object_caches:
                    self.create_object_cache(key, **meta)
                else:
                    # Ignore if the object cache is referenced to a different file.
                    if isinstance(meta, str):
                        continue

                    self._object_caches[key]['cache'].add_all(meta['values'])
                    self._object_caches[key][
                        'write_to_file'] = meta['write_to_file']
                    self._object_caches[key][
                        'separate_file'] = meta['separate_file']
                    self._object_caches[key]['can_reset'] = meta['can_reset']

    def write(self):
        """Persist the cache information to a yaml file."""
        with self._pod.profile.timer('Podcache.write'):
            if self._dependency_graph.is_dirty:
                output = self._dependency_graph.export()
                self._dependency_graph.mark_clean()
                self._write_json('{}{}'.format(
                    self._pod.PATH_CONTROL, self._pod.FILE_DEP_CACHE), output)

            if self._routes_cache.is_dirty:
                output = self._routes_cache.export()
                self._routes_cache.mark_clean()
                self._write_json('{}{}'.format(
                    self._pod.PATH_CONTROL, FILE_ROUTES_CACHE), output)

            # Write out any of the object caches configured for write_to_file.
            output = {}
            for key, meta in self._object_caches.items():
                if meta['write_to_file']:
                    cache_info = {
                        'can_reset': meta['can_reset'],
                        'write_to_file': meta['write_to_file'],
                        'values': meta['cache'].export(),
                        'separate_file': meta['separate_file'],
                    }
                    if meta['separate_file']:
                        filename = '/{}'.format(
                            object_cache.FILE_OBJECT_SUB_CACHE.format(key))
                        self._write_json(filename, cache_info)
                        output[key] = filename
                    else:
                        output[key] = cache_info
                    meta['cache'].mark_clean()
            if output:
                self._write_json('/{}'.format(FILE_OBJECT_CACHE), output)
