"""Tests for NVM Installer."""

import unittest
import mock
from grow.common import base_config
from grow.pods import pods
from grow import storage
from grow.sdk.installers import base_installer
from grow.sdk.installers import nvm_installer
from grow.testing import testing


class NvmInstallerTestCase(unittest.TestCase):
    """Test the Extensions Installer."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.installer = nvm_installer.NvmInstaller(
            self.pod, self.config)

    @mock.patch('subprocess.call')
    def test_check_prerequisites(self, mock_call):
        """Check prerequisites for nvm."""
        mock_call.return_value = 0
        self.installer.check_prerequisites()
        mock_call.assert_called_once_with(
            '. $NVM_DIR/nvm.sh && nvm --version > /dev/null 2>&1', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.call')
    def test_check_prerequisites_fail(self, mock_call):
        """Fails check prerequisites for nvm."""
        mock_call.return_value = 127
        with self.assertRaises(base_installer.MissingPrerequisiteError):
            self.installer.check_prerequisites()

    @mock.patch('subprocess.Popen')
    def test_install(self, mock_popen):
        """Installs using nvm."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        self.installer.install()
        print mock_popen.call_count
        calls = [
            mock.call(
                '. $NVM_DIR/nvm.sh && nvm install', **self.installer.subprocess_args(shell=True)),
        ]
        mock_popen.assert_has_calls(calls, any_order=True)

    @mock.patch('subprocess.Popen')
    def test_install_failed(self, mock_popen):
        """Install fails using nvm."""
        # Install fails.
        mock_process_install = mock.Mock()
        mock_process_install.wait.return_value = 1
        mock_popen.return_value = mock_process_install
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

        # Use fails.
        mock_process_install = mock.Mock()
        mock_process_install.wait.return_value = 0
        mock_process_use = mock.Mock()
        mock_process_use.wait.return_value = 1
        mock_popen.side_effects = [
            mock_process_install,
            mock_process_use,
        ]
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

    def test_should_run(self):
        """Detect if should run when using nvm."""
        self.assertFalse(self.installer.should_run)
        self.pod.write_file('.nvmrc', '')
        self.assertTrue(self.installer.should_run)
