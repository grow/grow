"""Tests for the rendered document."""

import unittest
from grow.rendering import rendered_document


class RenderPoolTestCase(unittest.TestCase):
    """Test the render pool."""

    @staticmethod
    def _create_doc(path, content=None):
        return rendered_document.RenderedDocument(path, content)

    def test_simple_content(self):
        """Simple content is stored."""
        doc = self._create_doc('/something', 'foobar')
        self.assertEqual('/something', doc.path)
        self.assertEqual('foobar', doc.read())
        self.assertNotEqual(None, doc.hash)

    def test_empty_content(self):
        """Simple content is stored."""
        doc = self._create_doc('/something', '')
        self.assertEqual('/something', doc.path)
        self.assertEqual('', doc.read())
        self.assertNotEqual(None, doc.hash)

    def test_none_content(self):
        """Simple content is stored."""
        doc = self._create_doc('/something', None)
        self.assertEqual('/something', doc.path)
        self.assertEqual(None, doc.read())
        self.assertEqual(None, doc.hash)


if __name__ == '__main__':
    unittest.main()
