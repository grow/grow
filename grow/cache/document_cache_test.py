"""Tests for the document cache."""

import unittest
from grow.cache import document_cache
from grow.testing import mocks


class DocumentCacheTestCase(unittest.TestCase):
    """Document Cache Tests."""

    def setUp(self):
        self.doc_cache = document_cache.DocumentCache()

    def test_add(self):
        """Add simple doc."""
        doc = mocks.mock_doc(pod_path='/content/pages/intro.md')
        self.doc_cache.add(doc, {
            'answer': 42
        })
        self.assertEqual(42, self.doc_cache.get(doc)['answer'])

    def test_add_all(self):
        """Add multiple docs."""
        doc = mocks.mock_doc(pod_path='/content/pages/intro.md')
        self.doc_cache.add_all({
            '/content/pages/intro.md': {
                'question': '???'
            }
        })
        self.assertEqual('???', self.doc_cache.get(doc)['question'])

    def test_add_property(self):
        """Add a property to a document cache."""
        doc = mocks.mock_doc(pod_path='/content/pages/intro.md')
        self.doc_cache.add_property(doc, 'answer', 42)
        self.assertEqual(42, self.doc_cache.get(doc)['answer'])

    def test_export(self):
        """Export cached document data."""
        doc = mocks.mock_doc(pod_path='/content/pages/intro.md')
        self.doc_cache.add(doc, {
            'answer': 42
        })
        doc = mocks.mock_doc(pod_path='/content/pages/about.md')
        self.doc_cache.add(doc, {
            'question': '???'
        })
        self.assertDictEqual({
            '/content/pages/about.md': {
                'question': '???'
            },
            '/content/pages/intro.md': {
                'answer': 42
            },
        }, self.doc_cache.export())

    def test_get_property(self):
        """Retrieve a property value."""
        doc = mocks.mock_doc(pod_path='/content/pages/intro.md')
        self.doc_cache.add(doc, {
            'answer': 42
        })
        self.assertEqual(42, self.doc_cache.get_property(doc, 'answer'))
        doc = mocks.mock_doc(pod_path='/content/pages/about.md')
        self.assertEqual(None, self.doc_cache.get_property(doc, 'answer'))

    def test_remove(self):
        """Remove a document from the cache."""
        value = {
            'answer': 42
        }
        doc = mocks.mock_doc(pod_path='/content/pages/intro.md')
        self.doc_cache.add(doc, value)
        self.assertEqual(42, self.doc_cache.get(doc)['answer'])
        self.assertEqual(value, self.doc_cache.remove(doc))
        self.assertEqual(None, self.doc_cache.get(doc))


if __name__ == '__main__':
    unittest.main()
