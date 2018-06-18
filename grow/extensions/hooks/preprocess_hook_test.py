"""Tests for preprocess hook."""

import unittest
from grow.extensions.hooks import preprocess_hook


class PreprocessHookTestCase(unittest.TestCase):
    """Test the preprocess hook."""

    def setUp(self):
        self.hook = preprocess_hook.PreprocessHook(None)

    def test_parse_config(self):
        """Correctly parses the config object."""
        self.assertEqual(self.hook.Config(), self.hook.parse_config({}))

    def test_should_trigger_autorun(self):
        """Should not trigger when not the autorun."""
        self.assertFalse(self.hook.should_trigger(
            None, {'autorun': False}, None, None, None))

    def test_should_trigger_autorun_all(self):
        """Should trigger when no autorun and running all."""
        self.assertTrue(self.hook.should_trigger(
            None, {'autorun': False}, None, None, True))

    def test_should_trigger_kind(self):
        """Should not trigger when not the same kind."""
        self.assertFalse(self.hook.should_trigger(
            None, {'kind': 'Something'}, None, None, None))

    def test_should_trigger_name(self):
        """Should not trigger when not the same kind."""
        self.assertTrue(self.hook.should_trigger(
            None, {'name': 'test'}, ['test'], None, None))

    def test_should_trigger_tags(self):
        """Should not trigger when not the same kind."""
        self.assertTrue(self.hook.should_trigger(
            None, {'tags': ['test']}, None, ['test'], None))

    def test_trigger(self):
        """Base hook triggers with no-op."""
        self.assertEqual(
            None, self.hook.trigger(None, {}, None, None, None, None))

    def test_trigger_previous_result(self):
        """Base hook triggers with no-op to previous result."""
        self.assertEqual(
            'Testing', self.hook.trigger('Testing', {}, None, None, None, None))
