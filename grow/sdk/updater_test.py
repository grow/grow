"""Tests for SDK Updater."""

import unittest
import mock
from grow.pods import pods
from grow import storage
from grow.sdk import updater
from grow.testing import testing


class UpdaterTestCase(unittest.TestCase):
    """Test the SDK Updater."""

    @staticmethod
    def _mock_json(mock_get, response):
        mock_json = mock.Mock(return_value=response)
        mock_get_result = mock.Mock()
        mock_get_result.json = mock_json
        mock_get.return_value = mock_get_result

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.updater = updater.Updater(self.pod)

    @mock.patch('grow.common.rc_config.RC_CONFIG')
    @mock.patch('grow.sdk.updater.Updater.current_version',
                new_callable=mock.PropertyMock)
    @mock.patch('grow.sdk.updater.Updater.latest_version',
                new_callable=mock.PropertyMock)
    def test_check_for_updates(self, mock_latest_version, mock_current_version, mock_config):
        """Update check works."""
        mock_config.needs_update_check = True
        mock_latest_version.return_value = '0.1.1'
        mock_current_version.return_value = '0.1.0'
        self.updater.check_for_updates()
        mock_config.write.assert_called()

    @mock.patch('os.execl')
    @mock.patch('subprocess.call')
    @mock.patch('grow.common.utils.is_packaged_app')
    @mock.patch('grow.common.rc_config.RC_CONFIG')
    @mock.patch('grow.sdk.updater.Updater.current_version',
                new_callable=mock.PropertyMock)
    @mock.patch('grow.sdk.updater.Updater.latest_version',
                new_callable=mock.PropertyMock)
    def test_check_for_updates_packaged_app(self, mock_latest_version, mock_current_version,
                                            mock_config, mock_is_packaged_app, mock_subprocess_call,
                                            mock_os_execl):
        """Update check works on packaged app."""
        mock_config.needs_update_check = True
        mock_is_packaged_app.return_value = True
        mock_latest_version.return_value = '0.1.1'
        mock_current_version.return_value = '0.1.0'
        mock_config.get.return_value = True
        mock_subprocess_call.return_value = 0
        mock_os_execl.return_value = True
        self.updater.check_for_updates(auto_update_prompt=True)
        mock_config.write.assert_called()

    @mock.patch('os.execl')
    @mock.patch('subprocess.call')
    @mock.patch('grow.common.utils.is_packaged_app')
    @mock.patch('grow.common.rc_config.RC_CONFIG')
    @mock.patch('grow.sdk.updater.Updater.current_version',
                new_callable=mock.PropertyMock)
    @mock.patch('grow.sdk.updater.Updater.latest_version',
                new_callable=mock.PropertyMock)
    def test_check_for_updates_packaged_app_restart_fail(
            self, mock_latest_version, mock_current_version, mock_config, mock_is_packaged_app,
            mock_subprocess_call, mock_os_execl):
        """Update check fails when error restarting."""
        mock_config.needs_update_check = True
        mock_is_packaged_app.return_value = True
        mock_latest_version.return_value = '0.1.1'
        mock_current_version.return_value = '0.1.0'
        mock_config.get.return_value = True
        mock_subprocess_call.return_value = 0
        mock_os_execl.side_effect = OSError()
        with self.assertRaises(SystemExit):
            self.updater.check_for_updates(auto_update_prompt=True)
        mock_config.write.assert_called()

    @mock.patch('os.execl')
    @mock.patch('subprocess.call')
    @mock.patch('grow.common.utils.is_packaged_app')
    @mock.patch('grow.common.rc_config.RC_CONFIG')
    @mock.patch('grow.sdk.updater.Updater.current_version',
                new_callable=mock.PropertyMock)
    @mock.patch('grow.sdk.updater.Updater.latest_version',
                new_callable=mock.PropertyMock)
    def test_check_for_updates_packaged_app_fail(self, mock_latest_version, mock_current_version,
                                                 mock_config, mock_is_packaged_app, mock_subprocess_call,
                                                 _mock_os_execl):
        """Update check fails when install fails."""
        mock_config.needs_update_check = True
        mock_is_packaged_app.return_value = True
        mock_latest_version.return_value = '0.1.1'
        mock_current_version.return_value = '0.1.0'
        mock_config.get.return_value = True
        mock_subprocess_call.return_value = 1
        with self.assertRaises(SystemExit):
            self.updater.check_for_updates(auto_update_prompt=True)
        mock_config.write.assert_called()

    @mock.patch('os.execl')
    @mock.patch('subprocess.call')
    @mock.patch('grow.common.utils.is_packaged_app')
    @mock.patch('grow.common.rc_config.RC_CONFIG')
    @mock.patch('grow.sdk.updater.Updater.current_version',
                new_callable=mock.PropertyMock)
    @mock.patch('grow.sdk.updater.Updater.latest_version',
                new_callable=mock.PropertyMock)
    def test_check_for_updates_no_update(self, mock_latest_version, mock_current_version,
                                         mock_config, mock_is_packaged_app, mock_subprocess_call,
                                         mock_os_execl):
        """Update check works when no need to update."""
        mock_config.needs_update_check = True
        mock_is_packaged_app.return_value = True
        mock_latest_version.return_value = '0.1.0'
        mock_current_version.return_value = '0.1.0'
        mock_subprocess_call.return_value = 0
        mock_os_execl.return_value = True
        self.updater.check_for_updates(auto_update_prompt=True)
        mock_config.write.assert_called()

    @mock.patch('os.execl')
    @mock.patch('subprocess.call')
    @mock.patch('grow.common.utils.is_packaged_app')
    @mock.patch('grow.common.rc_config.RC_CONFIG')
    @mock.patch('grow.sdk.updater.Updater.current_version',
                new_callable=mock.PropertyMock)
    @mock.patch('grow.sdk.updater.Updater.latest_version',
                new_callable=mock.PropertyMock)
    def test_check_for_updates_latest_fail(self, mock_latest_version, mock_current_version,
                                           mock_config, mock_is_packaged_app, mock_subprocess_call,
                                           mock_os_execl):
        """Update check works when cannot get latest version."""
        mock_config.needs_update_check = True
        mock_is_packaged_app.return_value = True
        mock_latest_version.side_effect = updater.LatestVersionCheckError()
        mock_current_version.return_value = '0.1.0'
        mock_subprocess_call.return_value = 0
        mock_os_execl.return_value = True
        self.updater.check_for_updates(auto_update_prompt=True)

    @mock.patch('os.execl')
    @mock.patch('subprocess.call')
    @mock.patch('grow.common.rc_config.RC_CONFIG')
    def test_check_for_updates_no_need(self, mock_config, mock_subprocess_call,
                                       mock_os_execl):
        """Update check is skipped for rate limiting."""
        mock_config.needs_update_check = False
        mock_config.get.return_value = True
        mock_subprocess_call.return_value = 0
        mock_os_execl.return_value = True
        self.updater.check_for_updates(auto_update_prompt=True)

    @mock.patch('requests.get')
    def test_latest_version_normal(self, mock_get):
        """Latest version check works."""
        self._mock_json(mock_get, [
            {
                'prerelease': False,
                'tag_name': '0.3.20',
                'assets': [
                    {
                        'name': 'Grow-SDK-Mac-0.3.20.zip',
                    },
                    {
                        'name': 'Grow-SDK-Linux-0.3.20.zip',
                    },
                ],
            },
        ])
        self.assertEqual('0.3.20', self.updater.latest_version)

    @mock.patch('requests.get')
    def test_latest_version_prerelease(self, mock_get):
        """Latest version check ignores prereleases."""
        self._mock_json(mock_get, [
            {
                'prerelease': True,
                'tag_name': '0.3.20',
                'assets': [
                    {
                        'name': 'Grow-SDK-Mac-0.3.20.zip',
                    },
                    {
                        'name': 'Grow-SDK-Linux-0.3.20.zip',
                    },
                ],
            },
            {
                'prerelease': False,
                'tag_name': '0.3.19',
                'assets': [
                    {
                        'name': 'Grow-SDK-Mac-0.3.19.zip',
                    },
                    {
                        'name': 'Grow-SDK-Linux-0.3.19.zip',
                    },
                ],
            },
        ])
        # Ignores prerelease
        self.assertEqual('0.3.19', self.updater.latest_version)

    @mock.patch('requests.get')
    def test_latest_version_missing(self, mock_get):
        """Latest version check fails when missing a valid platform asset."""
        self._mock_json(mock_get, [
            {
                'prerelease': False,
                'tag_name': '0.3.20',
                'assets': [
                    {
                        'name': 'Grow-SDK-Pear-0.3.20.zip',
                    },
                    {
                        'name': 'Grow-SDK-Unix-0.3.20.zip',
                    },
                ],
            },
        ])
        # Missing platform throws an error
        with self.assertRaises(updater.LatestVersionCheckError):
            _ = self.updater.latest_version

    @mock.patch('requests.get')
    def test_latest_version_message(self, mock_get):
        """Latest version check fails when a message is present in response."""
        self._mock_json(mock_get, {
            'message': 'Test'
        })
        with self.assertRaises(updater.LatestVersionCheckError):
            _ = self.updater.latest_version

    @mock.patch('requests.get')
    def test_latest_version_error(self, mock_get):
        """Latest version check fails on exception."""
        mock_get.side_effect = Exception('Testing')
        with self.assertRaises(updater.LatestVersionCheckError):
            _ = self.updater.latest_version
