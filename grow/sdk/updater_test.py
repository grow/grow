"""Tests for SDK Updater."""

import unittest
import mock
from grow.pods import pods
from grow.pods import storage
from grow.sdk import updater
from grow.testing import testing


class UpdaterTestCase(unittest.TestCase):
    """Test the SDK Updater."""

    def _mock_json(self, mock_get, response):
        mock_json = mock.Mock(return_value=response)
        mock_get_result = mock.Mock()
        mock_get_result.json = mock_json
        mock_get.return_value = mock_get_result

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.updater = updater.Updater(self.pod)

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
        """Latest version check works."""
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
        """Latest version check works."""
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
        """Latest version check works."""
        self._mock_json(mock_get, {
            'message': 'Test'
        })
        with self.assertRaises(updater.LatestVersionCheckError):
            _ = self.updater.latest_version
