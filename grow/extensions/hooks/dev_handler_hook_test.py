"""Tests for dev handler hook."""

import unittest
from grow.extensions.hooks import dev_handler_hook


class DevHandlerHookTestCase(unittest.TestCase):
    """Test the dev handler hook."""

    def setUp(self):
        self.hook = dev_handler_hook.DevHandlerHook(None)

    def test_trigger(self):
        """Base hook triggers with no-op."""
        self.assertEqual(
            None, self.hook.trigger(None, None))

    def test_trigger_previous_result(self):
        """Base hook triggers with no-op to previous result."""
        self.assertEqual(
            'Testing', self.hook.trigger('Testing', None))
