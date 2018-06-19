"""Tests for pre render hook."""

import unittest
from grow.extensions.hooks import pre_render_hook


class PreRenderHookTestCase(unittest.TestCase):
    """Test the pre render hook."""

    def setUp(self):
        self.hook = pre_render_hook.PreRenderHook(None)

    def test_trigger(self):
        """Base hook triggers with no-op."""
        self.assertEqual(
            None, self.hook.trigger(None, None, None))

    def test_trigger_previous_result(self):
        """Base hook triggers with no-op to previous result."""
        self.assertEqual(
            'Testing', self.hook.trigger('Testing', None, None))
