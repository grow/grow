"""Tests for Base Installer."""

import unittest
import mock
from grow.common import base_config
from grow.sdk import installer
from grow.sdk.installers import base_installer
from grow.sdk.installers import npm_installer
from grow.testing import mocks
from grow.testing import storage as test_storage


class InstallerTestCase(unittest.TestCase):
    """Test the Base Installer."""

    def setUp(self):
        self.test_fs = test_storage.TestFileStorage()
        self.installer = installer.Installer([])

    def test_failure(self):
        """Failure message formatting."""
        message = self.installer.failure('Bring Me Another Shrubbery!')
        expected = u'\x1b[38;5;1m\x1b[1m[✘] Bring Me Another Shrubbery!\x1b[0m'
        self.assertEqual(expected, message)

    def test_failure_with_extras(self):
        """Failure message formatting with extra messages."""
        message = self.installer.failure(
            'Bring Me Another Shrubbery!', extras=['1', 'A'])
        expected = u'\x1b[38;5;1m\x1b[1m[✘] Bring Me Another Shrubbery!\n   1\n   A\x1b[0m'
        self.assertEqual(expected, message)

    @mock.patch('subprocess.Popen')
    @mock.patch('subprocess.call')
    def test_run_installers(self, _mock_call, mock_popen):
        """Run installers successfully."""
        config = base_config.BaseConfig()
        mock_process = mock.Mock()
        mock_process.wait.return_value = None
        mock_popen.return_value = mock_process
        env = mocks.mock_env(name="testing")
        pod = mocks.mock_pod(
            env=env, root_path='/testing/', storage=self.test_fs.storage)
        self.test_fs.write('package.json', '')
        self.installer = installer.Installer([
            npm_installer.NpmInstaller(pod, config),
        ])
        self.assertTrue(self.installer.run_installers())

    @mock.patch('subprocess.Popen')
    @mock.patch('subprocess.call')
    def test_run_installers_not_run(self, _mock_call, _mock_popen):
        """Run installers runs even when installer should not run."""
        config = base_config.BaseConfig()
        env = mocks.mock_env(name="testing")
        pod = mocks.mock_pod(
            env=env, root_path='/testing/', storage=self.test_fs.storage)
        self.installer = installer.Installer([
            npm_installer.NpmInstaller(pod, config),
        ])
        self.assertTrue(self.installer.run_installers())

    @mock.patch('subprocess.Popen')
    @mock.patch('subprocess.call')
    def test_run_installers_dependency_fail(self, mock_call, _mock_popen):
        """Run installers with failing dependency check."""
        config = base_config.BaseConfig()
        logger = mock.Mock()
        mock_call.return_value = 127  # Simulate Yarn not found.
        env = mocks.mock_env(name="testing")
        pod = mocks.mock_pod(
            env=env, root_path='/testing/', storage=self.test_fs.storage)
        self.test_fs.write('package.json', '')
        self.installer = installer.Installer([
            npm_installer.NpmInstaller(pod, config),
        ], logger=logger)
        self.assertFalse(self.installer.run_installers())
        logger.error.assert_called()

    def test_success(self):
        """Success message formatting."""
        message = self.installer.success('Holy Hand Grenade')
        expected = u'\x1b[38;5;2m[✓] Holy Hand Grenade\x1b[0m'
        self.assertEqual(expected, message)

    def test_success_with_extras(self):
        """Success message formatting with extra messages."""
        message = self.installer.success('Holy Hand Grenade', extras=['1', 'A'])
        expected = u'\x1b[38;5;2m[✓] Holy Hand Grenade\n   1\n   A\x1b[0m'
        self.assertEqual(expected, message)
