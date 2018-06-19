"""Tests for post render hook."""

import unittest
from grow.extensions.hooks import post_render_hook


class PostRenderHookTestCase(unittest.TestCase):
    """Test the post render hook."""

    def setUp(self):
        self.hook = post_render_hook.PostRenderHook(None)

    def test_trigger(self):
        """Base hook triggers with no-op."""
        self.assertEqual(
            None, self.hook.trigger(None, None, None))

    def test_trigger_previous_result(self):
        """Base hook triggers with no-op to previous result."""
        self.assertEqual(
            'Testing', self.hook.trigger('Testing', None, None))
