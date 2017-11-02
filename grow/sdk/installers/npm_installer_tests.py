"""Tests for NPM Installer."""

import unittest
from grow.sdk.installers import npm_installer


class NpmInstallerTestCase(unittest.TestCase):
    """Test the Base Installer."""

    def setUp(self):
        self.installer = npm_installer.NpmInstaller()

    def test_should_run(self):
        """Test default for running the installer."""
        self.assertTrue(self.installer.should_run)
