"""Tests for Gerrit Installer."""

import unittest
import mock
from grow.common import base_config
from grow.common import utils
from grow.pods import pods
from grow import storage
from grow.sdk.installers import base_installer
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

    @mock.patch('subprocess.Popen')
    def test_install(self, mock_popen):
        """Installs using gerrit."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 0
        mock_popen.return_value = mock_process
        self.installer.install()
        is_found = {}
        for call in mock_popen.call_args_list:
            first_arg = call[0][0]
            if first_arg.startswith('curl -sLo'):
                is_found['curl'] = True
            if first_arg.startswith('chmod +x'):
                is_found['chmod'] = True
        self.assertTrue('curl' in is_found)
        self.assertTrue('chmod' in is_found)

    @mock.patch('subprocess.Popen')
    def test_install_failed(self, mock_popen):
        """Install fails using gerrit."""
        mock_process = mock.Mock()
        mock_process.wait.return_value = 1
        mock_popen.return_value = mock_process
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

        # Make sure that the chmod call failur also raises exception.
        mock_process.wait.side_effects = [0, 1]
        with self.assertRaises(base_installer.InstallError):
            self.installer.install()

    def test_should_run(self):
        """Detect if should run when using gerrit."""
        self.assertTrue(self.installer.should_run)
        self.config.set('gerrit', False)
        self.assertFalse(self.installer.should_run)

    @mock.patch.object(utils, 'get_git_repo')
    def test_should_run_git_remote(self, mock_get_repo):
        """Detect if should run when using gerrit and git remotes."""
        self.config.set('gerrit', None)

        # Works with no repo.
        mock_get_repo.return_value = None
        self.assertFalse(self.installer.should_run)

        def _create_remote_mock(url):
            mock_reader = mock.Mock()
            mock_reader.get.return_value = url
            mock_remote = mock.Mock(config_reader=mock_reader)
            return mock_remote

        # Works without the correct remote url.
        mock_repo = mock.Mock(remotes=[
            _create_remote_mock('git@github.com:something/repo.git'),
        ])
        mock_get_repo.return_value = mock_repo
        self.assertFalse(self.installer.should_run)

        # Works with the correct remote url.
        mock_repo = mock.Mock(remotes=[
            _create_remote_mock('git@github.com:something/repo.git'),
            _create_remote_mock('https://group.googlesource.com/something/repo'),
        ])
        mock_get_repo.return_value = mock_repo
        self.assertTrue(self.installer.should_run)
