"""Tests for dev file change hook."""

import unittest
from grow.extensions.hooks import dev_file_change_hook


class DevFileChangeHookTestCase(unittest.TestCase):
    """Test the dev file change hook."""

    def setUp(self):
        self.hook = dev_file_change_hook.DevFileChangeHook(None)

    def test_trigger(self):
        """Base hook triggers with no-op."""
        self.assertEqual(
            None, self.hook.trigger(None, '/content/pages/about.md'))

    def test_trigger_previous_result(self):
        """Base hook triggers with no-op to previous result."""
        self.assertEqual(
            'Testing', self.hook.trigger('Testing', '/content/pages/about.md'))
