"""Tests for Bower Installer."""

import unittest
import mock
from grow.common import base_config
from grow.sdk.installers import base_installer
from grow.sdk.installers import bower_installer
from grow.testing import mocks
from grow.testing import storage as test_storage


class BowerInstallerTestCase(unittest.TestCase):
    """Test the Bower Installer."""

    def _make_bower(self):
        self.test_fs.write('bower.json', '')

    def setUp(self):
        self.test_fs = test_storage.TestFileStorage()
        self.config = base_config.BaseConfig()
        env = mocks.mock_env(name="testing")
        self.pod = mocks.mock_pod(
            env=env, root_path='/testing/', storage=self.test_fs.storage)
        self.installer = bower_installer.BowerInstaller(
            self.pod, self.config)

    def tearDown(self):
        self.test_fs.tear_down()

    @mock.patch('subprocess.call')
    def test_check_prerequisites(self, mock_call):
        """Check prerequisites for bower."""
        mock_call.return_value = 0
        self.installer.check_prerequisites()
        mock_call.assert_called_once_with(
            'bower --version > /dev/null 2>&1', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.call')
    def test_check_prerequisites_fail(self, mock_call):
        """Fails check prerequisites for bower."""
        mock_call.return_value = 127
        with self.assertRaises(base_installer.MissingPrerequisiteError):
            self.installer.check_prerequisites()

    @mock.patch('subprocess.Popen')
    def test_install(self, mock_popen):
        """Installs using bower."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        self.installer.install()
        mock_popen.assert_called_once_with(
            'bower install', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.Popen')
    def test_install_failed(self, mock_popen):
        """Install fails using bower."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

    def test_should_run(self):
        """Detect if should run when using bower."""
        self.assertFalse(self.installer.should_run)
        self._make_bower()
        self.assertTrue(self.installer.should_run)
