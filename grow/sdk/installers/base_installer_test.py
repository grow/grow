"""Tests for Base Installer."""

import unittest
from grow.sdk.installers import base_installer


class BaseInstallerTestCase(unittest.TestCase):
    """Test the Base Installer."""

    def setUp(self):
        self.installer = base_installer.BaseInstaller()

    def test_post_install_messages(self):
        """Test default for install messages."""
        self.assertEqual(['Finished: None'], self.installer.post_install_messages)

    def test_should_run(self):
        """Test default for running the installer."""
        self.assertTrue(self.installer.should_run)

    def test_install(self):
        """Test install."""
        with self.assertRaises(NotImplementedError):
            self.installer.install()
