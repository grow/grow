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
        self.assertEquals('/something', doc.path)
        self.assertEquals('foobar', doc.read())
        self.assertNotEquals(None, doc.hash)

    def test_empty_content(self):
        """Simple content is stored."""
        doc = self._create_doc('/something', '')
        self.assertEquals('/something', doc.path)
        self.assertEquals('', doc.read())
        self.assertNotEquals(None, doc.hash)

    def test_none_content(self):
        """Simple content is stored."""
        doc = self._create_doc('/something', None)
        self.assertEquals('/something', doc.path)
        self.assertEquals(None, doc.read())
        self.assertEquals(None, doc.hash)


if __name__ == '__main__':
    unittest.main()
