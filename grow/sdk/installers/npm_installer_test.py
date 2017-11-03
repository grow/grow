"""Tests for NPM Installer."""

import unittest
from grow.common import base_config
from grow.pods import pods
from grow.pods import storage
from grow.sdk.installers import npm_installer
from grow.testing import testing


class NpmInstallerTestCase(unittest.TestCase):
    """Test the NPM Installer."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.installer = npm_installer.NpmInstaller(self.pod, self.config)

    def test_should_run(self):
        """Test if installer should run."""
        self.assertFalse(self.installer.should_run)
        self.pod.write_file('package.json', '')
        self.assertTrue(self.installer.should_run)

    def test_using_yarn_false(self):
        """Test if using yarn."""
        self.assertFalse(self.installer.using_yarn)

    def test_using_yarn_true(self):
        """Test if using yarn."""
        self.pod.write_file('yarn.lock', '')
        self.assertTrue(self.installer.using_yarn)
