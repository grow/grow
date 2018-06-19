"""Tests for extension controller."""

import unittest
from grow.extensions import extension_controller
from grow.extensions import base_extension
from grow.extensions import hooks


class TestHook(hooks.PostRenderHook):
    """Test hook."""

    def trigger(self, previous_result, doc, raw_content, *_args, **_kwargs):
        """Trigger the test hook."""
        return 'Triggered'


class TestExtensionOne(base_extension.BaseExtension):
    """Test extension."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [TestHook]


class TestExtensionTwo(base_extension.BaseExtension):
    """Test extension."""
    pass


class ExtensionControllerTestCase(unittest.TestCase):
    """Test the extension controller."""

    def test_register_extensions(self):
        """Registering extensions adds them to the controller."""
        ext_cont = extension_controller.ExtensionController(None)
        self.assertEqual(0, len(ext_cont))
        ext_cont.register_extensions([TestExtensionOne])
        self.assertEqual(1, len(ext_cont))
        ext_cont.register_extensions([TestExtensionOne, TestExtensionTwo])
        self.assertEqual(2, len(ext_cont))

    def test_trigger(self):
        """Trigger hooks from controller."""
        ext_cont = extension_controller.ExtensionController(None)
        ext_cont.register_extensions([TestExtensionOne])
        self.assertEqual(
            'Triggered', ext_cont.trigger('post_render', None, None))
