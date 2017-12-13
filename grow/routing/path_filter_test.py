"""Tests for the path filter."""

import unittest
import mock
from grow.routing import path_filter


class PathFilterTestCase(unittest.TestCase):
    """Test the routes."""

    def setUp(self):
        self.filter = path_filter.PathFilter()

    def test_filter_defaults(self):
        """Default filters work."""
        # Normal files work.
        self.assertTrue(self.filter.is_valid('/sitemap.xml'))
        self.assertTrue(self.filter.is_valid('/index.html'))
        self.assertTrue(self.filter.is_valid('/static/images/logo.png'))
        self.assertTrue(self.filter.is_valid('/.grow/index.html'))

        # Dot files should be ignored.
        self.assertFalse(self.filter.is_valid('/.DS_STORE'))
        self.assertFalse(self.filter.is_valid('/.htaccess'))

    @mock.patch('grow.routing.path_filter.DEFAULT_INCLUDED', [1, 2])
    @mock.patch('grow.routing.path_filter.DEFAULT_IGNORED', [3, 4])
    def test_filter_default_filters(self):
        """Default filters work."""
        self.assertEqual([1, 2], list(self.filter.included))
        self.assertEqual([3, 4], list(self.filter.ignored))

    def test_filter_ignores(self):
        """Simple ignore filters work."""
        self.filter.add_ignored('foo.bar')

        # Normal files work.
        self.assertTrue(self.filter.is_valid('/sitemap.xml'))
        self.assertTrue(self.filter.is_valid('/index.html'))
        self.assertTrue(self.filter.is_valid('/static/images/logo.png'))
        self.assertTrue(self.filter.is_valid('/.grow/index.html'))

        # Defaults are not kept.
        self.assertTrue(self.filter.is_valid('/.DS_STORE'))
        self.assertTrue(self.filter.is_valid('/.htaccess'))

        # Custom filters work.
        self.assertFalse(self.filter.is_valid('/foo.bar'))
        self.assertFalse(self.filter.is_valid('/foo/bar/foo.bar'))

    def test_filter_included(self):
        """Simple included filters work."""
        self.filter.add_ignored('foo.bar')
        self.filter.add_included('/bar/foo.bar')

        # Normal files work.
        self.assertTrue(self.filter.is_valid('/sitemap.xml'))
        self.assertTrue(self.filter.is_valid('/index.html'))
        self.assertTrue(self.filter.is_valid('/static/images/logo.png'))
        self.assertTrue(self.filter.is_valid('/.grow/index.html'))

        # Defaults are not kept.
        self.assertTrue(self.filter.is_valid('/.DS_STORE'))
        self.assertTrue(self.filter.is_valid('/.htaccess'))

        # Custom filters work.
        self.assertFalse(self.filter.is_valid('/foo.bar'))

        # Included filter overrides the ignores.
        self.assertTrue(self.filter.is_valid('/foo/bar/foo.bar'))

    def test_filter_constructor(self):
        """Simple ignore filters work."""
        self.filter = path_filter.PathFilter(
            ['foo.bar'], ['/bar/foo.bar'])

        # Normal files work.
        self.assertTrue(self.filter.is_valid('/sitemap.xml'))
        self.assertTrue(self.filter.is_valid('/index.html'))
        self.assertTrue(self.filter.is_valid('/static/images/logo.png'))
        self.assertTrue(self.filter.is_valid('/.grow/index.html'))

        # Defaults are not kept.
        self.assertTrue(self.filter.is_valid('/.DS_STORE'))
        self.assertTrue(self.filter.is_valid('/.htaccess'))

        # Custom filters work.
        self.assertFalse(self.filter.is_valid('/foo.bar'))

        # Included filter overrides the ignores.
        self.assertTrue(self.filter.is_valid('/foo/bar/foo.bar'))
