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
