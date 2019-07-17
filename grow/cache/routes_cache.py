"""
Cache for storing and retrieving routing information in a pod.
"""

FILE_ROUTES_CACHE = 'routescache.json'
EXPORT_KEY = 'routes'
VERSION = 1


class RoutesCache(object):
    """Routes cache for caching routing data."""

    def __init__(self):
        self._cache = {}
        self._is_dirty = False

    @staticmethod
    def _export_cache(routes):
        routing_info = {}
        for env, env_routes in routes.items():
            routing_info[env] = {}
            for path, item in env_routes.items():
                try:
                    value = item['value'].export()
                except AttributeError:
                    value = item['value']
                routing_info[env][path] = {
                    'value': value,
                    'options': item['options'],
                }
        return routing_info

    def add(self, key, value, options=None, env=None):
        """Add a new item to the cache or overwrite an existing value."""
        if env not in self._cache:
            self._cache[env] = {}
        cache = self._cache[env]
        cache_value = {
            'value': value,
            'options': options,
        }
        if not self._is_dirty and (key not in cache or cache[key] != cache_value):
            self._is_dirty = True
        cache[key] = cache_value

    def export(self):
        """Returns the raw cache data."""
        return {
            'version': VERSION,
            EXPORT_KEY: self._export_cache(self._cache),
        }

    def from_data(self, data, generator):
        """Set the cache from data."""
        # Check for version changes in the data format.
        version = data.get('version')
        if not version or version < VERSION:
            return

        for env, env_data in data[EXPORT_KEY].items():
            for key, item in env_data.items():
                self.add(
                    key, generator(item['value']),
                    options=item['options'], env=env)

    def get(self, key, env=None):
        """Retrieve the value from the cache."""
        return self._cache.get(env, {}).get(key, None)

    @property
    def is_dirty(self):
        """Have the contents of the object cache been modified?"""
        return self._is_dirty

    def mark_clean(self):
        """Mark that the object cache is clean."""
        self._is_dirty = False

    def remove(self, key, env=None):
        """Removes a single element from the cache."""
        self._is_dirty = True
        return self._cache.get(env, {}).pop(key, None)

    def reset(self):
        """Reset the internal cache object."""
        self._cache = {}
        self._is_dirty = False
