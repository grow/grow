"""Tests for the rendered document."""

import unittest
from grow.rendering import rendered_document


class RenderPoolTestCase(unittest.TestCase):
    """Test the render pool."""

    @staticmethod
    def _create_doc(path, content=None):
        return rendered_document.RenderedDocument(path, content)

    def test_rendered_document(self):
        """."""
        pass


if __name__ == '__main__':
    unittest.main()
