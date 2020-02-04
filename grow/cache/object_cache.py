"""
Cache for storing and retrieving data in a pod.

Supports arbitrary data based on a cache key.

The contents of the cache should be raw and not internationalized as it will
be shared between locales.
"""

import re
from grow.common import structures


FILE_OBJECT_CACHE = 'objectcache.json'
FILE_OBJECT_SUB_CACHE = 'objectcache.{}.json'


class ObjectCache(object):
    """Object cache for caching arbitrary data in a pod."""

    SENTINEL = '~!~!~!~!~!'

    def __contains__(self, key):
        key = self._memcached_key(key)
        value = self._cache.get(key, self.SENTINEL)
        return value != self.SENTINEL

    def __init__(self):
        self._local_cache = structures.LocalMemcachedCache()
        self._memcached_client = None
        self._memcached_prefix = None
        self._memcached_keys = set()
        self._is_dirty = False

    @property
    def _cache(self):
        if self.memcached:
            return self.memcached
        return self._local_cache

    @property
    def is_dirty(self):
        """Have the contents of the object cache been modified?"""
        return self._is_dirty

    @property
    def memcached(self):
        """Get the memcached client."""
        return self._memcached_client

    def _memcached_key(self, key):
        """Create the prefixed key for memcached usage."""
        if self._memcached_prefix:
            key = '{}.{}'.format(self._memcached_prefix, key)
        return key

    def _memcached_unkey(self, key):
        """Undo the prefixed key for memcached usage."""
        if self._memcached_prefix:
            return key[len(self._memcached_prefix)+1:]
        return key

    def add(self, key, value):
        """Add a new item to the cache or overwrite an existing value."""
        key = self._memcached_key(key)
        self._memcached_keys.add(key)
        existing_value = self._cache.get(key, self.SENTINEL)
        if not self._is_dirty and existing_value != value:
            self._is_dirty = True
        self._cache.add(key, value)

    def add_all(self, key_to_cached):
        """Update the cache with a preexisting set of data."""
        if self.memcached:
            mem_key_to_cached = {}
            for key, value in key_to_cached.items():
                key = self._memcached_key(key)
                mem_key_to_cached[key] = value
                self._memcached_keys.add(key)

            self.memcached.set_many(mem_key_to_cached)
        else:
            for key, value in key_to_cached.items():
                self.add(key, value)

    def export(self):
        """Returns the raw cache data."""
        if self.memcached:
            raise NotImplementedError('export unavailable when using memcached')
        return self._cache.data

    def get(self, key):
        """Retrieve the value from the cache."""
        key = self._memcached_key(key)
        return self._cache.get(key, None)

    def mark_clean(self):
        """Mark that the object cache is clean."""
        self._is_dirty = False

    def remove(self, key):
        """Removes a single element from the cache."""
        key = self._memcached_key(key)
        cached_value = self._cache.get(key)
        self._is_dirty = True
        self._cache.delete(key)
        return cached_value

    def reset(self):
        """Reset the internal cache object."""

        if self.memcached:
            self.memcached.delete_many(self._memcached_keys)
            self._memcached_keys = set()
            self._is_dirty = False
            return

        self._local_cache = structures.LocalMemcachedCache()
        self._is_dirty = False

    def search(self, pattern):
        """Search through the cache and return all the matching elements."""

        if self.memcached:
            raise NotImplementedError('search unavailable when using memcached')

        if type(pattern) is not type(re.compile('.')):
            pattern = re.compile(pattern)

        results = {}

        for key, value in self._cache.data.items():
            if pattern.search(key) is not None:
                results[key] = value

        return results

    def set_memcached(self, client, prefix=None):
        """Set the memcached client and define the prefix."""
        self._memcached_client = client
        self._memcached_prefix = prefix

        # Put all the local existing values into memcache.
        for key, value in self._local_cache.data.items():
            self.add(key, value)
