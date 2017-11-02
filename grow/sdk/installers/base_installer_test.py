"""Tests for Base Installer."""

import os
import unittest
from grow.common import base_config
from grow.pods import env as environment
from grow.pods import pods
from grow.pods import storage
from grow.sdk.installers import base_installer
from grow.testing import testing


class BaseInstallerTestCase(unittest.TestCase):
    """Test the Base Installer."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.installer = base_installer.BaseInstaller(self.pod, self.config)

    def test_subprocess_args(self):
        """Test subprocess args."""
        args = self.installer.subprocess_args()
        ending = os.path.join('node_modules', '.bin')
        self.assertTrue(args['env']['PATH'].endswith(ending))
        self.assertFalse('GROW_ENVIRONMENT_NAME' in args['env'])

    def test_subprocess_args_env_name(self):
        """Test subprocess args env name."""
        self.pod.set_env(environment.Env(environment.EnvConfig(name='testing')))
        args = self.installer.subprocess_args()
        self.assertEqual(args['env']['GROW_ENVIRONMENT_NAME'], 'testing')

    def test_subprocess_shell(self):
        """Test subprocess args with shell."""
        args = self.installer.subprocess_args(shell=True)
        self.assertTrue(args['shell'])

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
