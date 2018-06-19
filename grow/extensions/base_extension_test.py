"""Tests for base extension."""

import unittest
from grow.extensions import base_extension
from grow.extensions import hooks


class TestHook(hooks.DevFileChangeHook):
    """Test hook."""

    def trigger(self, previous_result, pod_path, *_args, **_kwargs):
        """Trigger the test hook."""
        return previous_result


class TestExtension(base_extension.BaseExtension):
    """Test extension."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [TestHook]


class TestExtensionTwo(TestExtension):
    """Test extension."""

    def dev_file_change_hook(self):
        """Manually create the hook to test the auto_hook."""
        return TestHook(self)


class BaseExtensionTestCase(unittest.TestCase):
    """Test the base extension."""

    def test_auto_hook(self):
        """Automatically finds the correct hook class."""
        ext = base_extension.BaseExtension(None, {})
        with self.assertRaises(base_extension.MissingHookError):
            ext.auto_hook('testing')

    def test_config_disabled(self):
        """Uses the disabled config."""
        ext = base_extension.BaseExtension(None, {
            'disabled': [
                'a',
            ],
            'enabled': [
                'a',
            ],
        })
        self.assertFalse(ext.hooks.is_enabled('a'))
        self.assertFalse(ext.hooks.is_enabled('b'))

    def test_config_enabled(self):
        """Uses the enabled config."""
        ext = base_extension.BaseExtension(None, {
            'enabled': [
                'a',
            ],
        })
        self.assertTrue(ext.hooks.is_enabled('a'))
        self.assertFalse(ext.hooks.is_enabled('b'))

    def test_no_config(self):
        """Uses empty config."""
        ext = base_extension.BaseExtension(None, {})
        self.assertFalse(ext.hooks.is_enabled('a'))
        self.assertFalse(ext.hooks.is_enabled('b'))

    def test_sample_extension(self):
        """Test a stub extension."""
        ext = TestExtension(None, {})
        self.assertTrue(ext.hooks.is_enabled('dev_file_change'))
        hook = ext.auto_hook('dev_file_change')
        self.assertIsInstance(hook, TestHook)

    def test_sample_extension_two(self):
        """Test a stub extension with hook method."""
        ext = TestExtensionTwo(None, {})
        self.assertTrue(ext.hooks.is_enabled('dev_file_change'))
        hook = ext.auto_hook('dev_file_change')
        self.assertIsInstance(hook, TestHook)
