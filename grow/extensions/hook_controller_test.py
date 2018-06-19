"""Tests for hook controller."""

import unittest
from grow.extensions import base_extension
from grow.extensions import hook_controller
from grow.extensions import hooks


class TestHook(hooks.DevFileChangeHook):
    """Test hook."""

    def trigger(self, previous_result, pod_path, *_args, **_kwargs):
        """Trigger the test hook."""
        return 'Testing'


class TestExtension(base_extension.BaseExtension):
    """Test extension."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [TestHook]


class HookControllerTestCase(unittest.TestCase):
    """Test the hook controller."""

    def test_register_extensions(self):
        """Registering extensions completes correctly."""
        cont = hook_controller.HookController('dev_file_change')
        self.assertEqual(0, len(cont))
        cont.register_extensions([
            TestExtension(None, {})
        ])
        self.assertEqual(1, len(cont))

    def test_trigger(self):
        """Registering extensions completes correctly."""
        ext = TestExtension(None, {})
        hook = TestHook(ext)
        cont = hook_controller.HookController('dev_file_change', default_hook=hook)
        self.assertEqual(1, len(cont))

        result = cont.trigger('/content/page/about.md')
        self.assertEqual('Testing', result)
