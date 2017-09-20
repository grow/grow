"""
Cache for storing and retrieving data specific to a document.

Supports caching specific to the pod_path of a document.

The contents of the cache should be raw and not internationalized as it will
be shared between locales with the same pod_path.
"""

class DocumentCache(object):

    def __init__(self):
        self.reset()

    def _ensure_exists(self, doc, value=None):
        if doc.pod_path not in self._cache:
            self._cache[doc.pod_path] = value or {}
        return doc.pod_path

    def add(self, doc, value):
        self._cache[doc.pod_path] = value

    def add_all(self, path_to_cached):
        for path, value in path_to_cached.iteritems():
            self._cache[path] = value

    def add_property(self, doc, prop, value):
        path = self._ensure_exists(doc)
        self._cache[path][prop] = value

    def remove(self, doc):
        return self.remove_by_path(doc.pod_path)

    def remove_by_path(self, path):
        return self._cache.pop(path, None)

    def export(self):
        return self._cache

    def get(self, doc):
        return self._cache.get(doc.pod_path, None)

    def get_property(self, doc, prop):
        if doc.pod_path in self._cache:
            return self._cache[doc.pod_path].get(prop, None)
        return None

    def reset(self):
        self._cache = {}
