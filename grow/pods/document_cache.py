"""
Cache for storing and retrieving data specific to a document.

Supports caching specific to the pod_path and locale of a document.
"""

class DocumentCache(object):

    def __init__(self):
        self.reset()

    def _ensure_exists_locale(self, doc, value=None):
        path, locale = self._get_parts(doc)
        self._ensure_exists_path(doc)
        if locale not in self._cache[path]:
            self._cache[path][locale] = value or {}
        return path, locale

    def _ensure_exists_path(self, doc, value=None):
        path, _ = self._get_parts(doc)
        if path not in self._cache:
            self._cache[path] = value or {}
        return path

    def _get_parts(self, doc):
        locale = str(doc._locale_kwarg)
        return doc.pod_path, locale if locale != 'None' else None

    def add(self, doc, cached):
        self._ensure_exists_locale(doc, value=cached)

    def add_all(self, path_to_locale_to_cached):
        for path, locales in path_to_locale_to_cached.iteritems():
            if path not in self._cache:
                self._cache[path] = {}
            for locale, value in locales.iteritems():
                self._cache[path][locale] = value

    def add_property(self, doc, prop, value):
        path, locale = self._ensure_exists_locale(doc)
        self._cache[path][locale][prop] = value

    def delete(self, doc):
        path, _ = self._get_parts(doc)
        return self.delete_by_path(path)

    def delete_by_path(self, path):
        return self._cache.pop(path, None)

    def export(self):
        return self._cache

    def get(self, doc):
        path, locale = self._get_parts(doc)
        if path in self._cache:
            if locale in self._cache[path]:
                return self._cache[path][locale]
        return None

    def get_property(self, doc, prop):
        path, locale = self._get_parts(doc)
        if path in self._cache:
            if locale in self._cache[path]:
                return self._cache[path][locale].get(prop, None)
        return None

    def reset(self):
        self._cache = {}
