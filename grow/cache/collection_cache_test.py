"""Tests for the collection cache."""

import unittest
from grow import storage
from grow.cache import collection_cache
from grow.pods import pods
from grow.testing import testing


class DocumentCacheTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_add_collection(self):
        col_cache = collection_cache.CollectionCache()
        col = self.pod.get_collection('pages')
        col_cache.add_collection(col)
        self.assertEquals(col, col_cache.get_collection('pages'))

    def test_add_document(self):
        col_cache = collection_cache.CollectionCache()
        doc = self.pod.get_doc('/content/pages/intro.md')
        col = doc.collection
        col_cache.add_document(doc)
        self.assertEquals(doc, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))

    def test_remove_by_path(self):
        col_cache = collection_cache.CollectionCache()
        doc = self.pod.get_doc('/content/pages/intro.md')
        col = doc.collection
        col_cache.add_document(doc)

        # Deleting a document's path removes the document.
        self.assertEquals(doc, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))
        col_cache.remove_by_path('/content/pages/intro.md')
        self.assertEquals(None, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))

        # Deleting a collection blueprint removes the entire collection.
        col_cache.add_collection(col)
        self.assertEquals(col, col_cache.get_collection('pages'))
        col_cache.remove_by_path('/content/pages/_blueprint.yaml')
        self.assertEquals(None, col_cache.get_collection('pages'))

    def test_remove_collection(self):
        col_cache = collection_cache.CollectionCache()
        doc = self.pod.get_doc('/content/pages/intro.md')
        col = doc.collection

        # Test straight up remove.
        col_cache.add_collection(col)
        self.assertEquals(col, col_cache.get_collection('pages'))
        col_cache.remove_collection(col)
        self.assertEquals(None, col_cache.get_collection('pages'))

        # Test that documents in the collection are removed.
        col_cache.add_document(doc)
        self.assertEquals(doc, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))
        col_cache.remove_collection(col)
        self.assertEquals(None, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))

    def test_remove_document(self):
        col_cache = collection_cache.CollectionCache()
        doc = self.pod.get_doc('/content/pages/intro.md')
        col = doc.collection
        col_cache.add_document(doc)
        self.assertEquals(doc, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))
        col_cache.remove_document(doc)
        self.assertEquals(None, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))

    def test_remove_document_locales(self):
        col_cache = collection_cache.CollectionCache()
        doc = self.pod.get_doc('/content/pages/intro.md')
        col_cache.add_document(doc)
        doc_it = self.pod.get_doc('/content/pages/intro.md', 'it')
        col_cache.add_document(doc_it)
        col = doc.collection
        self.assertEquals(doc, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))
        self.assertEquals(doc_it, col_cache.get_document(
            col, '/content/pages/intro.md', doc_it.locale_safe))
        col_cache.remove_document_locales(doc)
        self.assertEquals(None, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))
        self.assertEquals(None, col_cache.get_document(
            col, '/content/pages/intro.md', doc_it.locale_safe))

    def test_get_collection(self):
        col_cache = collection_cache.CollectionCache()
        self.assertEquals(None, col_cache.get_collection('pages'))
        col = self.pod.get_collection('pages')
        col_cache.add_collection(col)
        self.assertEquals(col, col_cache.get_collection('pages'))

    def test_get_document(self):
        col_cache = collection_cache.CollectionCache()
        doc = self.pod.get_doc('/content/pages/intro.md')
        col = doc.collection
        self.assertEquals(None, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))
        col_cache.add_document(doc)
        self.assertEquals(doc, col_cache.get_document(
            col, '/content/pages/intro.md', doc.locale_safe))


if __name__ == '__main__':
    unittest.main()
