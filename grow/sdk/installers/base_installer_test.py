"""Tests for Base Installer."""

import unittest
from grow.common import base_config
from grow.sdk.installers import base_installer
from grow.testing import mocks


class BaseInstallerTestCase(unittest.TestCase):
    """Test the Base Installer."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.pod = mocks.mock_pod()
        self.installer = base_installer.BaseInstaller(self.pod, self.config)

    def test_post_install_messages(self):
        """Default for install messages."""
        self.assertEqual(['Finished: None'], self.installer.post_install_messages)

    def test_should_run(self):
        """Default for running the installer."""
        self.assertTrue(self.installer.should_run)

    def test_install(self):
        """Fails without implmented install."""
        with self.assertRaises(NotImplementedError):
            self.installer.install()
