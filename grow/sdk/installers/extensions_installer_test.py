"""Tests for Extensions Installer."""

import unittest
import mock
from grow.common import base_config
from grow.pods import pods
from grow import storage
from grow.sdk.installers import base_installer
from grow.sdk.installers import extensions_installer
from grow.testing import testing


class ExtensionsInstallerTestCase(unittest.TestCase):
    """Test the Extensions Installer."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.installer = extensions_installer.ExtensionsInstaller(
            self.pod, self.config)

    @mock.patch('subprocess.call')
    def test_check_prerequisites(self, mock_call):
        """Check prerequisites for extensions."""
        mock_call.return_value = 0
        self.installer.check_prerequisites()
        mock_call.assert_called_once_with(
            'pip --version > /dev/null 2>&1', **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.call')
    def test_check_prerequisites_fail(self, mock_call):
        """Fails check prerequisites for extensions."""
        mock_call.return_value = 127
        with self.assertRaises(base_installer.MissingPrerequisiteError):
            self.installer.check_prerequisites()

    @mock.patch('subprocess.Popen')
    def test_install(self, mock_popen):
        """Installs extensions using pip."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        extensions_dir = self.pod.extensions_dir
        extensions_init_file = '/{}/__init__.py'.format(extensions_dir)
        self.pod.delete_file(extensions_init_file)
        self.assertFalse(self.pod.file_exists(extensions_init_file))
        self.installer.install()
        self.assertTrue(self.pod.file_exists(extensions_init_file))
        expected = 'pip install -U -t {} -r extensions.txt'.format(
            extensions_dir)
        mock_popen.assert_called_once_with(
            expected, **self.installer.subprocess_args(shell=True))

    @mock.patch('subprocess.Popen')
    def test_install_failed(self, mock_popen):
        """Install extensions fail using pip."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

    def test_should_run(self):
        """Detect if should run when installing extensions."""
        self.assertFalse(self.installer.should_run)
        self.pod.write_file('extensions.txt', '')
        self.assertTrue(self.installer.should_run)
