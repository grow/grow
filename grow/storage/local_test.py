"""Tests for the local file storage."""

import errno
import os  # pylint: disable=unused-import
import unittest
import mock
from grow.storage import base as grow_base
from grow.storage import local as grow_local
from grow.testing import storage as test_storage


class LocalStorageCleanTestCase(unittest.TestCase):
    """Test the local file storage cleaning abilities."""

    def setUp(self):
        self.test_fs = test_storage.TestFileStorage()
        self.storage = grow_local.LocalStorage(self.test_fs.content_dir)

    def tearDown(self):
        self.test_fs.tear_down()

    def test_validate_path(self):
        """Local storage validate path."""
        # And converts the / to the backslash separator.
        sep = '/'

        # Paths inside the root_dir work ok.
        self.storage.validate_path(
            '{}{sep}podspec.yaml'.format(self.test_fs.content_dir, sep=sep),
            sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('/tmp/somewhere/', sep=sep)


class LocalStorageTestCase(unittest.TestCase):
    """Test the local file storage."""

    def setUp(self):
        self.test_fs = test_storage.TestFileStorage()
        self.storage = grow_local.LocalStorage(self.test_fs.content_dir)

    def tearDown(self):
        self.test_fs.tear_down()

    def test_copy_file(self):
        """Local storage copy file."""
        self.test_fs.write('podspec.yaml', 'test: true')
        expected = ['podspec.yaml']
        actual = self.storage.list_dir('/')
        actual.sort()
        self.assertListEqual(expected, actual)

        self.storage.copy_file('podspec.yaml', 'podspec-copy.yaml')

        expected = ['podspec.yaml', 'podspec-copy.yaml']
        expected.sort()
        actual = self.storage.list_dir('/')
        actual.sort()
        self.assertListEqual(expected, actual)

    def test_copy_files(self):
        """Local storage copy files."""
        self.test_fs.write('podspec.yaml', 'test: true')
        expected = ['podspec.yaml']
        actual = self.storage.list_dir('/')
        actual.sort()
        self.assertListEqual(expected, actual)

        self.storage.copy_files({'podspec.yaml': 'podspec-copy.yaml'})

        expected = ['podspec.yaml', 'podspec-copy.yaml']
        expected.sort()
        actual = self.storage.list_dir('/')
        actual.sort()
        self.assertListEqual(expected, actual)

    def test_delete_dir(self):
        """Local storage delete directory."""
        self.test_fs.write('content/index.yaml', 'test: true')
        expected = ['index.yaml']
        actual = self.storage.list_dir('content')
        self.assertEqual(expected, actual)

        self.storage.delete_dir('content/')

        expected = []
        actual = self.storage.list_dir('content')
        self.assertEqual(expected, actual)

        # Deleting a non-existant directory does not error.
        self.storage.delete_dir('content/')

    def test_delete_file(self):
        """Local storage delete file."""
        # Non-existant file does not error.
        self.assertFalse(self.storage.file_exists('podspec.yaml'))
        self.storage.delete_file('podspec.yaml')

        # Existing file is deleted.
        self.test_fs.write('podspec.yaml', 'test: true')
        self.assertTrue(self.storage.file_exists('podspec.yaml'))
        self.storage.delete_file('podspec.yaml')
        self.assertFalse(self.storage.file_exists('podspec.yaml'))

    def test_file_exists(self):
        """Local storage deterime if file exists."""
        self.assertFalse(self.storage.file_exists('podspec.yaml'))
        self.test_fs.write('podspec.yaml', 'test: true')
        self.assertTrue(self.storage.file_exists('podspec.yaml'))

    def test_file_size(self):
        """Local storage read file size."""
        self.test_fs.write('podspec.yaml', 'test: true')
        self.assertEqual(10, self.storage.file_size('podspec.yaml'))

    def test_list_dir(self):
        """Local storage list directory."""
        expected = []
        actual = self.storage.list_dir('content')
        self.assertEqual(expected, actual)

        self.test_fs.write('content/write.yaml', 'test: true')
        expected = ['write.yaml']
        actual = self.storage.list_dir('content')
        self.assertEqual(expected, actual)

        # Recursive
        self.test_fs.write('podspec.yaml', 'test: true')
        expected = ['podspec.yaml', 'content/write.yaml']
        actual = self.storage.list_dir('/', recursive=True)
        self.assertEqual(expected, actual)

    def test_move_file(self):
        """Local storage move file."""
        self.test_fs.write('podspec.yaml', 'test: true')
        expected = ['podspec.yaml']
        actual = self.storage.list_dir('/')
        actual.sort()
        self.assertListEqual(expected, actual)

        self.storage.move_file('podspec.yaml', 'podspec-move.yaml')

        expected = ['podspec-move.yaml']
        actual = self.storage.list_dir('/')
        self.assertListEqual(expected, actual)

    def test_move_files(self):
        """Local storage move files."""
        self.test_fs.write('podspec.yaml', 'test: true')
        expected = ['podspec.yaml']
        actual = self.storage.list_dir('/')
        actual.sort()
        self.assertListEqual(expected, actual)

        self.storage.move_files({'podspec.yaml': 'podspec-move.yaml'})

        expected = ['podspec-move.yaml']
        actual = self.storage.list_dir('/')
        self.assertListEqual(expected, actual)

    def test_read_file(self):
        """Local storage read file."""
        expected = 'title: Testing Storage'
        self.test_fs.write('podspec.yaml', expected)
        actual = self.storage.read_file('podspec.yaml')
        self.assertEqual(actual, expected)

    def test_read_files(self):
        """Local storage read multiple files."""
        expected = {
            '/podspec.yaml': 'title: Testing Storage\n',
        }
        self.test_fs.write('podspec.yaml', expected['/podspec.yaml'])
        actual = self.storage.read_files('podspec.yaml')
        self.assertEqual(actual, expected)

    def test_remote_storage(self):
        """Local storage is not a remote type storage."""
        self.assertFalse(self.storage.IS_REMOTE_STORAGE)

    def test_walk(self):
        """Local storage walk."""
        self.test_fs.write('podspec.yaml', 'test: true')
        self.test_fs.write('content/index.yaml', 'test: true')

        paths = []
        for root, _, files in self.storage.walk('/'):
            for filename in files:
                paths.append('{}{}'.format(root, filename))
        self.assertEqual(2, len(paths))

    def test_write_file(self):
        """Local storage write file."""
        self.storage.write_file('content/write.yaml', 'test: true')
        actual = self.storage.read_file('content/write.yaml')
        expected = 'test: true'
        self.assertEqual(actual, expected)

        # Works correctly with existing directory.
        self.storage.write_file('content/write.yaml', 'test: true')

    @mock.patch('os.makedirs')
    def test_write_file_fail(self, mock_makedirs):
        """Local storage write file with failure."""
        mock_makedirs.side_effect = OSError(errno.EPERM, 'You shall not pass!')
        with self.assertRaises(OSError):
            self.storage.write_file('content/write.yaml', 'test: true')


if __name__ == '__main__':
    unittest.main()
