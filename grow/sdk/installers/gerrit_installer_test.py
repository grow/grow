"""Tests for Gerrit Installer."""

import unittest
from grow.common import base_config
from grow.pods import pods
from grow.pods import storage
from grow.sdk.installers import gerrit_installer
from grow.testing import testing


class GerritInstallerTestCase(unittest.TestCase):
    """Test the Extensions Installer."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.config.set('gerrit', True)
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.installer = gerrit_installer.GerritInstaller(
            self.pod, self.config)

    def test_should_run(self):
        """Test if installer should run."""
        self.assertTrue(self.installer.should_run)
        self.config.set('gerrit', False)
        self.assertFalse(self.installer.should_run)
