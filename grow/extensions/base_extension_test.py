"""Tests for base extension."""

import unittest
from grow.extensions import base_extension


class BaseExtensionTestCase(unittest.TestCase):
    """Test the base extension."""

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

    def test_dev_handler_hook(self):
        """Not implemented post render hook."""
        ext = base_extension.BaseExtension(None, {})
        with self.assertRaises(NotImplementedError):
            ext.dev_handler_hook()

    def test_post_render_hook(self):
        """Not implemented post render hook."""
        ext = base_extension.BaseExtension(None, {})
        with self.assertRaises(NotImplementedError):
            ext.post_render_hook()
