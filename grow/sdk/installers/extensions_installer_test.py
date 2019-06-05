"""Tests for Extensions Installer."""

import unittest
import mock
from grow.common import base_config
from grow.sdk.installers import base_installer
from grow.sdk.installers import extensions_installer
from grow.testing import mocks
from grow.testing import storage as test_storage


class ExtensionsInstallerTestCase(unittest.TestCase):
    """Test the Extensions Installer."""

    def _make_extensions(self):
        self.test_fs.write('extensions.txt', '')

    def setUp(self):
        self.test_fs = test_storage.TestFileStorage()
        self.config = base_config.BaseConfig()
        env = mocks.mock_env(name="testing")
        self.pod = mocks.mock_pod(
            env=env, root_path='/testing/', storage=self.test_fs.storage)
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
        self.installer.install()
        self.pod.storage.file_exists('/extensions/__init__.py')
        expected = 'pip install -U -t {} -r extensions.txt'.format(
            'extensions')
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

    def test_post_install_messages(self):
        """Install messages."""
        self.assertEqual(['Finished: Extensions -> extensions/'], self.installer.post_install_messages)

    def test_should_run(self):
        """Detect if should run when installing extensions."""
        self.assertFalse(self.installer.should_run)
        self._make_extensions()
        self.assertTrue(self.installer.should_run)
