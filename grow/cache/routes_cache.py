"""
Cache for storing and retrieving routing information in a pod.
"""

from grow.routing import router


FILE_ROUTES_CACHE = 'routescache.json'


class RoutesCache(object):
    """Routes cache for caching routing data in a pod."""

    KEY_CONCRETE = 'concrete'
    KEY_DYNAMIC = 'dynamic'

    def __init__(self):
        self._cache = {
            self.KEY_CONCRETE: {},
            self.KEY_DYNAMIC: {},
        }
        self._is_dirty = False

    @classmethod
    def _cache_key(cls, is_concrete):
        return cls.KEY_CONCRETE if is_concrete else cls.KEY_DYNAMIC

    @staticmethod
    def _export_cache(routes):
        routing_info = {}
        for path, item in routes.iteritems():
            value = item['value'].export() if hasattr(item['value'], 'export') else item['value']
            routing_info[path] = {
                'value': value,
                'options': item['options'],
            }
        return routing_info

    def add(self, key, value, options=None, is_concrete=False):
        """Add a new item to the cache or overwrite an existing value."""
        cache = self._cache[self._cache_key(is_concrete)]
        if not self._is_dirty and (key not in cache or cache[key] != value):
            self._is_dirty = True
        cache[key] = {
            'value': value,
            'options': options,
        }

    def export(self, is_concrete=None):
        """Returns the raw cache data."""
        if is_concrete is None:
            return {
                self.KEY_CONCRETE: self._export_cache(self._cache[self.KEY_CONCRETE]),
                self.KEY_DYNAMIC: self._export_cache(self._cache[self.KEY_DYNAMIC]),
            }
        if is_concrete:
            return self._export_cache(self._cache[self.KEY_CONCRETE])
        return self._export_cache(self._cache[self.KEY_DYNAMIC])

    def from_data(self, data):
        """Set the cache from data."""
        for super_key in [self.KEY_DYNAMIC, self.KEY_CONCRETE]:
            if super_key in data:
                is_concrete = super_key == self.KEY_CONCRETE
                for key, item in data[super_key].iteritems():
                    self.add(
                        key,
                        router.RouteInfo.from_data(**item['value']),
                        options=item['options'], is_concrete=is_concrete)

    def get(self, key, is_concrete=False):
        """Retrieve the value from the cache."""
        return self._cache[self._cache_key(is_concrete)].get(key, None)

    @property
    def is_dirty(self):
        """Have the contents of the object cache been modified?"""
        return self._is_dirty

    def mark_clean(self):
        """Mark that the object cache is clean."""
        self._is_dirty = False

    def raw(self, is_concrete=None):
        """Returns the raw cache data."""
        if is_concrete is None:
            return self._cache
        if is_concrete:
            return self._cache[self.KEY_CONCRETE]
        return self._cache[self.KEY_DYNAMIC]

    def remove(self, key, is_concrete=False):
        """Removes a single element from the cache."""
        self._is_dirty = True
        return self._cache[self._cache_key(is_concrete)].pop(key, None)

    def reset(self):
        """Reset the internal cache object."""
        self._cache = {
            self.KEY_CONCRETE: {},
            self.KEY_DYNAMIC: {},
        }
        self._is_dirty = False
