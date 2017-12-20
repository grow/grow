"""Cache for storing and retrieving data specific to collections.

Supports caching the collection and caching documents within those collections.
"""

import os
import threading
from grow.collections import collection


class CollectionCache(object):

    def __init__(self):
        self.reset()
        self._lock = threading.RLock()

    @staticmethod
    def generate_cache_key(pod_path, locale):
        return '{}::{}'.format(pod_path, locale)

    def add_collection(self, col):
        self._cache[col.collection_path] = {
            'collection': col,
            'docs': {},
        }

    def add_document(self, doc):
        col = doc.collection
        self.ensure_collection(col)
        # NOTE: Using `doc.locale` causes infinite loop since it needs to load
        # the fields (which can have circular dependencies).
        cache_key = CollectionCache.generate_cache_key(
            doc.pod_path, doc.locale_safe)
        self._cache[col.collection_path]['docs'][cache_key] = doc

    def add_document_locale(self, doc, locale):
        """Force a doc to be saved to a specific locale.

        When docs have a default locale that differs from the collection default
        it causes issues since the cache does not know that None locale is not correct.
        This allows for the None locale to be forced to the default locale from the
        doc.
        """
        col = doc.collection
        self.ensure_collection(col)
        cache_key = CollectionCache.generate_cache_key(
            doc.pod_path, locale)
        self._cache[col.collection_path]['docs'][cache_key] = doc

    def remove_by_path(self, path):
        """Removes the collection or document based on the path."""
        if path.startswith(collection.Collection.CONTENT_PATH):
            if path.endswith(
                    '/{}'.format(collection.Collection.BLUEPRINT_PATH)):
                # If this is a blueprint then remove the entire collection.
                col_path = path[len(collection.Collection.CONTENT_PATH):]
                # Get just the directory.
                col_path = os.path.split(col_path)[0]
                collection_path = col_path[1:]  # Remove /
                with self._lock:
                    if collection_path in self._cache:
                        del self._cache[collection_path]
            else:
                # Search for an existing collection path.
                col_path = path[len(collection.Collection.CONTENT_PATH):]
                col_path = os.path.split(col_path)[0]
                while col_path != os.sep:
                    collection_path = col_path[1:]
                    with self._lock:
                        if collection_path in self._cache:
                            # Do a 'wildcard' match on the path to remove all
                            # locales.
                            generic_key = CollectionCache.generate_cache_key(
                                path, '')
                            for key in self._cache[collection_path]['docs'].keys():
                                if key.startswith(generic_key):
                                    del self._cache[
                                        collection_path]['docs'][key]
                                    return
                    col_path = os.path.split(col_path)[0]

    def remove_collection(self, col):
        with self._lock:
            if col.collection_path in self._cache:
                del self._cache[col.collection_path]

    def remove_document(self, doc):
        col = doc.collection
        with self._lock:
            if col.collection_path in self._cache:
                cache_key = CollectionCache.generate_cache_key(
                    doc.pod_path, doc.locale_safe)
                if cache_key in self._cache[col.collection_path]['docs']:
                    del self._cache[col.collection_path]['docs'][cache_key]

    def remove_document_locale(self, doc, locale):
        col = doc.collection
        with self._lock:
            if col.collection_path in self._cache:
                cache_key = CollectionCache.generate_cache_key(
                    doc.pod_path, locale)
                if cache_key in self._cache[col.collection_path]['docs']:
                    del self._cache[col.collection_path]['docs'][cache_key]

    def remove_document_locales(self, doc):
        col = doc.collection
        with self._lock:
            if col.collection_path in self._cache:
                doc_cache_key = CollectionCache.generate_cache_key(
                    doc.pod_path, '')
                invalid_keys = []
                for cache_key in self._cache[col.collection_path]['docs'].iterkeys():
                    if cache_key.startswith(doc_cache_key):
                        invalid_keys.append(cache_key)
                for cache_key in invalid_keys:
                    del self._cache[col.collection_path]['docs'][cache_key]

    def ensure_collection(self, col):
        with self._lock:
            if col.collection_path not in self._cache:
                self.add_collection(col)

    def get_collection(self, collection_path):
        collection_path = collection.Collection.clean_collection_path(
            collection_path)
        if collection_path in self._cache:
            return self._cache[collection_path]['collection']
        return None

    def get_document(self, col, pod_path, locale):
        if col.collection_path in self._cache:
            cache_key = CollectionCache.generate_cache_key(pod_path, locale)
            return self._cache[col.collection_path]['docs'].get(
                cache_key, None)
        return None

    def reset(self):
        self._cache = {}
