"""Lightweight in-memory cache compatible with Jinja2 bytecode caching."""

import time


class SimpleCache:
    """In-memory key-value cache with optional per-item expiration."""

    def __init__(self, threshold=500, default_timeout=300):
        self._cache = {}
        self._threshold = threshold
        self.default_timeout = default_timeout

    def _normalize_timeout(self, timeout):
        if timeout is None:
            timeout = self.default_timeout
        if timeout > 0:
            return time.monotonic() + timeout
        return 0

    def _prune(self):
        if len(self._cache) <= self._threshold:
            return
        now = time.monotonic()
        expired = [k for k, (exp, _) in self._cache.items() if exp != 0 and exp <= now]
        for k in expired:
            del self._cache[k]
        while len(self._cache) > self._threshold:
            self._cache.pop(next(iter(self._cache)))

    def get(self, key):
        entry = self._cache.get(key)
        if entry is None:
            return None
        expires, value = entry
        if expires == 0 or expires > time.monotonic():
            return value
        del self._cache[key]
        return None

    def set(self, key, value, timeout=None):
        expires = self._normalize_timeout(timeout)
        self._prune()
        self._cache[key] = (expires, value)
        return True

    def add(self, key, value, timeout=None):
        if self.has(key):
            return False
        return self.set(key, value, timeout=timeout)

    def delete(self, key):
        return self._cache.pop(key, None) is not None

    def clear(self):
        self._cache.clear()
        return True

    def has(self, key):
        entry = self._cache.get(key)
        if entry is None:
            return False
        expires, _ = entry
        if expires == 0 or expires > time.monotonic():
            return True
        del self._cache[key]
        return False

    def get_many(self, *keys):
        return [self.get(k) for k in keys]

    def set_many(self, mapping, timeout=None):
        for k, v in mapping.items():
            self.set(k, v, timeout=timeout)
        return True
