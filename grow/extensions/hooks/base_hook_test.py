"""Tests for base hook."""

import unittest
import mock
from grow.extensions.hooks import base_hook
from grow.testing import mocks


class BaseHookTestCase(unittest.TestCase):
    """Test the base hook."""

    def setUp(self):
        self.pod = mocks.mock_pod()
        extension = mock.Mock()
        type(extension).pod = mock.PropertyMock(return_value=self.pod)
        self.hook = base_hook.BaseHook(extension)

    def test_pod(self):
        """Shortcut to reference the pod."""
        self.assertEqual(self.pod, self.hook.pod)

    def test_should_trigger(self):
        """Default should always trigger."""
        self.assertEqual(True, self.hook.should_trigger(None))

    def test_trigger(self):
        """Nothing to trigger by default."""
        with self.assertRaises(NotImplementedError):
            self.hook.trigger(None)
