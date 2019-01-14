"""Tests for features."""

import unittest
from grow.common import features


class FeaturesTestCase(unittest.TestCase):
    """Test the features control."""

    def test_default_enabled(self):
        """Does the default enabled work?"""
        feat = features.Features(default_enabled=True)
        self.assertTrue(feat.is_enabled('unknown'))

    def test_default_enabled_false(self):
        """Does the default disabled work?"""
        feat = features.Features(default_enabled=False)
        self.assertFalse(feat.is_enabled('unknown'))

    def test_disable(self):
        """Disabling feature."""
        feat = features.Features(default_enabled=True)
        self.assertTrue(feat.is_enabled('a'))
        feat.disable('a')
        self.assertFalse(feat.is_enabled('a'))

    def test_enable(self):
        """Enabling feature."""
        feat = features.Features(default_enabled=False)
        self.assertFalse(feat.is_enabled('a'))
        feat.enable('a')
        self.assertTrue(feat.is_enabled('a'))

    def test_enable_with_config(self):
        """Enabling feature with a config."""
        feat = features.Features(default_enabled=False)
        self.assertFalse(feat.is_enabled('a'))
        feat.enable('a', {'config': True})
        self.assertTrue(feat.is_enabled('a'))
        self.assertEqual({'config': True}, feat.config('a').export())

    def test_enable_without_config(self):
        """Enabling feature without a config."""
        feat = features.Features(default_enabled=False)
        self.assertFalse(feat.is_enabled('a'))
        feat.enable('a')
        self.assertTrue(feat.is_enabled('a'))
        self.assertEqual({}, feat.config('a').export())

    def test_is_disabled_disabled(self):
        """Enabled features."""
        feat = features.Features(disabled=['a', 'b'])
        self.assertTrue(feat.is_disabled('a'))
        self.assertTrue(feat.is_disabled('b'))
        self.assertFalse(feat.is_disabled('c'))

    def test_is_disabled_disabled_with_default_enabled_false(self):
        """Enabled features."""
        feat = features.Features(disabled=['a', 'b'], default_enabled=False)
        self.assertTrue(feat.is_disabled('a'))
        self.assertTrue(feat.is_disabled('b'))
        self.assertTrue(feat.is_disabled('c'))

    def test_is_disabled_enabled(self):
        """Enabled features."""
        feat = features.Features(enabled=['a', 'b'])
        self.assertFalse(feat.is_disabled('a'))
        self.assertFalse(feat.is_disabled('b'))
        self.assertFalse(feat.is_disabled('c'))

    def test_is_disabled_enabled_with_default_enabled_false(self):
        """Enabled features."""
        feat = features.Features(enabled=['a', 'b'], default_enabled=False)
        self.assertFalse(feat.is_disabled('a'))
        self.assertFalse(feat.is_disabled('b'))
        self.assertTrue(feat.is_disabled('c'))

    def test_is_enabled_disabled(self):
        """Enabled features."""
        feat = features.Features(disabled=['a', 'b'])
        self.assertFalse(feat.is_enabled('a'))
        self.assertFalse(feat.is_enabled('b'))
        self.assertTrue(feat.is_enabled('c'))

    def test_is_enabled_disabled_with_default_enabled_false(self):
        """Enabled features."""
        feat = features.Features(disabled=['a', 'b'], default_enabled=False)
        self.assertFalse(feat.is_enabled('a'))
        self.assertFalse(feat.is_enabled('b'))
        self.assertFalse(feat.is_enabled('c'))

    def test_is_enabled_enabled(self):
        """Enabled features."""
        feat = features.Features(enabled=['a', 'b'])
        self.assertTrue(feat.is_enabled('a'))
        self.assertTrue(feat.is_enabled('b'))
        self.assertTrue(feat.is_enabled('c'))

    def test_is_enabled_enabled_with_default_enabled_false(self):
        """Enabled features."""
        feat = features.Features(enabled=['a', 'b'], default_enabled=False)
        self.assertTrue(feat.is_enabled('a'))
        self.assertTrue(feat.is_enabled('b'))
        self.assertFalse(feat.is_enabled('c'))

    def test_callable_enabled(self):
        """Callable shortcut for testing for enabled features."""
        feat = features.Features(enabled=['a'], default_enabled=False)
        self.assertTrue(feat('a'))
        self.assertFalse(feat('b'))
