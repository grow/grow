"""
Cache for storing and retrieving data in a pod.

Supports arbitrary data based on a cache key.

The contents of the cache should be raw and not internationalized as it will
be shared between locales.
"""

import re

class ObjectCache(object):
    """Object cache for caching arbitrary data in a pod."""

    def __contains__(self, key):
        return key in self._cache

    def __init__(self):
        self.reset()

    def add(self, key, value):
        """Add a new item to the cache or overwrite an existing value."""
        self._cache[key] = value

    def add_all(self, key_to_cached):
        """Update the cache with a preexisting set of data."""
        self._cache.update(key_to_cached)

    def remove(self, key):
        """Removes a single element from the cache."""
        return self._cache.pop(key)

    def export(self):
        """Returns the raw cache data."""
        return self._cache

    def get(self, key):
        """Retrieve the value from the cache."""
        return self._cache.get(key, None)

    def reset(self):
        """Reset the internal cache object."""
        self._cache = {}

    def search(self, pattern):
        """Search through the cache and return all the matching elements."""
        if type(pattern) is not type(re.compile('.')):
            pattern = re.compile(pattern)

        results = {}

        for key, value in self._cache.iteritems():
            if pattern.search(key) is not None:
                results[key] = value

        return results
