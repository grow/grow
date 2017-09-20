"""
Cache for storing and retrieving file content at a pod_path.

The contents of the cache should be raw and not internationalized as it will
be shared between locales with the same pod_path.
"""

class FileCache(object):
    """Simple cache for file contents."""

    def __init__(self):
        self.reset()

    def add(self, pod_path, value):
        """Add a value to the cache by pod_path."""
        self._cache[pod_path] = value

    def add_all(self, pod_path_to_cached):
        """Add a multiple values to the cache by pod_paths."""
        for pod_path, value in pod_path_to_cached.iteritems():
            self._cache[pod_path] = value

    def remove(self, pod_path):
        """Remove a value from the cache by pod_path."""
        return self._cache.pop(pod_path, None)

    def export(self):
        """Exports all the file cache data."""
        return self._cache

    def get(self, pod_path):
        """Retrieve a cache value by pod_path or None."""
        return self._cache.get(pod_path, None)

    def path_changed(self, pod_path):
        """Triggers that a path has changed and the value is invalid."""
        return self.remove(pod_path)

    def reset(self):
        """Resets the internal cache reference."""
        self._cache = {}
