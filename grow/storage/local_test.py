"""Tests for the local file storage."""

import errno
import shutil
import os
import unittest
import mock
from grow.storage import local as grow_local


class LocalStorageTestCase(unittest.TestCase):
    """Test the local file storage."""

    def setUp(self):
        # Cleanup from old tests.
        dynamic_dir = 'grow/storage/testdata/dynamic'
        try:
            shutil.rmtree(dynamic_dir)
        except FileNotFoundError:
            pass
        os.makedirs(dynamic_dir)

        self.storage = grow_local.LocalStorage('grow/storage/testdata')

    def test_copy_file(self):
        """Local storage copy."""
        with self.assertRaises(NotImplementedError):
            self.storage.copy_file('podspec.yaml', 'podspec-copy.yaml')

    def test_delete_dir(self):
        """Local storage delete directory."""
        with self.assertRaises(NotImplementedError):
            self.storage.delete_dir('content/')

    def test_delete_file(self):
        """Local storage delete file."""
        with self.assertRaises(NotImplementedError):
            self.storage.delete_file('podspec.yaml')

    def test_file_exists(self):
        """Local storage deterime if file exists."""
        with self.assertRaises(NotImplementedError):
            self.storage.file_exists('podspec.yaml')

    def test_file_size(self):
        """Local storage read file size."""
        with self.assertRaises(NotImplementedError):
            self.storage.file_size('podspec.yaml')

    def test_list_dir(self):
        """Local storage list directory."""
        with self.assertRaises(NotImplementedError):
            self.storage.list_dir('content/')

    def test_move_file(self):
        """Local storage move file."""
        with self.assertRaises(NotImplementedError):
            self.storage.move_file('podspec.yaml', 'podspec-move.yaml')

    def test_read_file(self):
        """Local storage read file."""
        actual = self.storage.read_file('podspec.yaml')
        expected = 'title: Testing Storage\n'
        self.assertEqual(actual, expected)

    def test_read_files(self):
        """Local storage read multiple files."""
        actual = self.storage.read_files('podspec.yaml')
        expected = {
            '/podspec.yaml': 'title: Testing Storage\n',
        }
        self.assertEqual(actual, expected)

    def test_remote_storage(self):
        """Local storage is not a remote type storage."""
        self.assertFalse(self.storage.IS_REMOTE_STORAGE)

    def test_walk(self):
        """Local storage walk."""
        with self.assertRaises(NotImplementedError):
            self.storage.walk('content/')

    def test_write_file(self):
        """Local storage write file."""
        self.storage.write_file('dynamic/write.yaml', 'test: true')
        actual = self.storage.read_file('dynamic/write.yaml')
        expected = 'test: true'
        self.assertEqual(actual, expected)

    @mock.patch('os.makedirs')
    def test_write_file_fail(self, mock_makedirs):
        """Local storage write file with failure."""
        mock_makedirs.side_effect = OSError(errno.EPERM, 'You shall not pass!')
        with self.assertRaises(OSError):
            self.storage.write_file('dynamic/write.yaml', 'test: true')


if __name__ == '__main__':
    unittest.main()
