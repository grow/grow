"""Tests for Themes."""

import os
import unittest
import zipfile
import mock
from grow.sdk import themes
from grow.testing import testing


TEST_ZIP_FILE = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__), '..', 'testing', 'testdata', 'themes', 'base-master.zip'))


class ThemesTestCase(unittest.TestCase):
    """Test the Themes."""

    def setUp(self):
        self.pod = testing.create_pod()

    @mock.patch('grow.sdk.themes.GrowTheme.archive',
                new_callable=mock.PropertyMock)
    def test_extract(self, mock_archive):
        """Test theme unpacking."""
        mock_archive.return_value = zipfile.ZipFile(TEST_ZIP_FILE, 'r')
        self.assertFalse(self.pod.file_exists('/podspec.yaml'))
        theme = themes.GrowTheme('base')
        theme.extract(self.pod)
        self.assertTrue(self.pod.file_exists('/podspec.yaml'))
