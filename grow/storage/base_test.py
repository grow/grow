"""Tests for the base file storage."""

import unittest
from grow.storage import base as grow_base


class BaseStorageTestCase(unittest.TestCase):
    """Test the routes."""

    def setUp(self):
        self.storage = grow_base.BaseStorage()

    def test_copy_file(self):
        """Base storage copy."""
        with self.assertRaises(NotImplementedError):
            self.storage.copy_file('podspec.yaml', 'podspec-copy.yaml')

    def test_delete_dir(self):
        """Base storage delete directory."""
        with self.assertRaises(NotImplementedError):
            self.storage.delete_dir('content/')

    def test_delete_file(self):
        """Base storage delete file."""
        with self.assertRaises(NotImplementedError):
            self.storage.delete_file('podspec.yaml')

    def test_file_exists(self):
        """Base storage deterime if file exists."""
        with self.assertRaises(NotImplementedError):
            self.storage.file_exists('podspec.yaml')

    def test_file_size(self):
        """Base storage read file size."""
        with self.assertRaises(NotImplementedError):
            self.storage.file_size('podspec.yaml')

    def test_list_dir(self):
        """Base storage list directory."""
        with self.assertRaises(NotImplementedError):
            self.storage.list_dir('content/')

    def test_move_file(self):
        """Base storage move file."""
        with self.assertRaises(NotImplementedError):
            self.storage.move_file('podspec.yaml', 'podspec-move.yaml')

    def test_read_file(self):
        """Base storage read file."""
        with self.assertRaises(NotImplementedError):
            self.storage.read_file('podspec.yaml')

    def test_read_files(self):
        """Base storage read multiple files."""
        with self.assertRaises(NotImplementedError):
            self.storage.read_files('podspec.yaml', 'package.json')

    def test_remote_storage(self):
        """Base storage is a remote type storage."""
        self.assertFalse(self.storage.IS_REMOTE_STORAGE)

    def test_walk(self):
        """Base storage walk."""
        with self.assertRaises(NotImplementedError):
            self.storage.walk('content/')

    def test_write_file(self):
        """Base storage write file."""
        with self.assertRaises(NotImplementedError):
            self.storage.write_file('podspec.yaml', 'test: true')


if __name__ == '__main__':
    unittest.main()
