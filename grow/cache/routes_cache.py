"""
Cache for storing and retrieving routing information in a pod.
"""

from grow.routing import router


FILE_ROUTES_CACHE = 'routescache.json'


class RoutesCache(object):
    """Routes cache for caching routing data in a pod."""

    KEY_CONCRETE = 'concrete'
    KEY_DYNAMIC = 'dynamic'
    KEY_NONE = '__None__'

    def __init__(self):
        self._cache = {
            self.KEY_CONCRETE: {},
            self.KEY_DYNAMIC: {},
        }
        self._is_dirty = False

    @classmethod
    def _cache_key(cls, concrete):
        return cls.KEY_CONCRETE if concrete else cls.KEY_DYNAMIC

    @staticmethod
    def _export_cache(routes):
        routing_info = {}
        for env, env_routes in routes.items():
            routing_info[env] = {}
            for path, item in env_routes.items():
                if hasattr(item['value'], 'export'):
                    value = item['value'].export()
                else:
                    value = item['value']
                routing_info[env][path] = {
                    'value': value,
                    'options': item['options'],
                }
        return routing_info

    def add(self, key, value, options=None, concrete=False, env=None):
        """Add a new item to the cache or overwrite an existing value."""
        if env is None:
            env = self.KEY_NONE
        cache_key = self._cache_key(concrete)
        if env not in self._cache[cache_key]:
            self._cache[cache_key][env] = {}
        cache = self._cache[cache_key][env]
        cache_value = {
            'value': value,
            'options': options,
        }
        if not self._is_dirty and (key not in cache or cache[key] != cache_value):
            self._is_dirty = True
        cache[key] = cache_value

    def export(self, concrete=None):
        """Returns the raw cache data."""
        if concrete is None:
            return {
                'version': 1,
                self.KEY_CONCRETE: self._export_cache(self._cache[self.KEY_CONCRETE]),
                self.KEY_DYNAMIC: self._export_cache(self._cache[self.KEY_DYNAMIC]),
            }
        return self._export_cache(self._cache[self._cache_key(concrete)])

    def from_data(self, data):
        """Set the cache from data."""
        # Check for version changes in the data format.
        version = data.get('version')
        if not version or version < 1:
            return

        for super_key in [self.KEY_DYNAMIC, self.KEY_CONCRETE]:
            if super_key in data:
                concrete = super_key == self.KEY_CONCRETE
                for env, env_data in data[super_key].items():
                    for key, item in env_data.items():
                        self.add(
                            key,
                            router.RouteInfo.from_data(**item['value']),
                            options=item['options'], concrete=concrete,
                            env=env)

    def get(self, key, concrete=False, env=None):
        """Retrieve the value from the cache."""
        if env is None:
            env = self.KEY_NONE
        return self._cache[self._cache_key(concrete)].get(env, {}).get(key, None)

    @property
    def is_dirty(self):
        """Have the contents of the object cache been modified?"""
        return self._is_dirty

    def mark_clean(self):
        """Mark that the object cache is clean."""
        self._is_dirty = False

    def raw(self, concrete=None, env=None):
        """Returns the raw cache data."""
        if concrete is None:
            return self._cache
        if env is None:
            env = self.KEY_NONE
        return self._cache[self._cache_key(concrete)].get(env, {})

    def remove(self, key, concrete=False, env=None):
        """Removes a single element from the cache."""
        if env is None:
            env = self.KEY_NONE
        self._is_dirty = True
        return self._cache[self._cache_key(concrete)].get(env, {}).pop(key, None)

    def reset(self):
        """Reset the internal cache object."""
        self._cache = {
            self.KEY_CONCRETE: {},
            self.KEY_DYNAMIC: {},
        }
        self._is_dirty = False
