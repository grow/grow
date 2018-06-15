"""
Cache for storing and retrieving file content at a pod_path.

The contents of the cache can be parsed and are stored based on locale.
"""

class FileCache(object):
    """Simple cache for file contents."""

    def __init__(self):
        self.reset()

    def _ensure_exists(self, pod_path, value=None):
        if pod_path not in self._cache:
            self._cache[pod_path] = value or {}
        return self._cache[pod_path]

    def add(self, pod_path, value, locale=None):
        """Add a value to the cache by pod_path."""
        container = self._ensure_exists(pod_path)
        container[locale] = value

    def add_all(self, pod_path_to_cached, locale=None):
        """Add a multiple values to the cache by pod_paths."""
        for pod_path, value in pod_path_to_cached.iteritems():
            container = self._ensure_exists(pod_path)
            container[locale] = value

    def remove(self, pod_path):
        """Remove a value from the cache by pod_path."""
        return self._cache.pop(pod_path, None)

    def export(self):
        """Exports all the file cache data."""
        return self._cache

    def get(self, pod_path, locale=None):
        """Retrieve a cache value by pod_path or None."""
        container = self._ensure_exists(pod_path)
        return container.get(locale, None)

    def reset(self):
        """Resets the internal cache reference."""
        self._cache = {}
