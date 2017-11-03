"""Tests for Gulp Installer."""

import unittest
from grow.common import base_config
from grow.pods import pods
from grow.pods import storage
from grow.sdk.installers import gulp_installer
from grow.testing import testing


class GulpInstallerTestCase(unittest.TestCase):
    """Test the Gulp Installer."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.installer = gulp_installer.GulpInstaller(
            self.pod, self.config)

    def test_should_run(self):
        """Test if installer should run."""
        self.assertFalse(self.installer.should_run)
        self.pod.write_file('gulpfile.js', '')
        self.assertTrue(self.installer.should_run)
