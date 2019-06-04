"""Tests for the base file storage."""

import unittest
from grow.storage import base as grow_base


class BaseStorageCleanTestCase(unittest.TestCase):
    """Test the base storage cleaning abilities."""

    def setUp(self):
        self.storage = grow_base.BaseStorage('grow/storage/testdata')

    def test_clean_directory(self):
        """Base storage clean directory."""
        # Always ends with the separator.
        # And converts the / to the os separator.
        sep = '/'
        self.assertEqual(
            sep, self.storage.clean_directory('', sep=sep))
        self.assertEqual(
            sep, self.storage.clean_directory('/', sep=sep))
        self.assertEqual(
            'base{sep}'.format(sep=sep),
            self.storage.clean_directory('base', sep=sep))
        self.assertEqual(
            'base{sep}'.format(sep=sep),
            self.storage.clean_directory('base/', sep=sep))
        self.assertEqual(
            'foo{sep}bar{sep}'.format(sep=sep),
            self.storage.clean_directory('foo/bar', sep=sep))
        self.assertEqual(
            'foo{sep}bar{sep}'.format(sep=sep),
            self.storage.clean_directory('foo/bar/', sep=sep))

    def test_clean_directory_backslash(self):
        """Base storage clean directory with backslash."""
        # Always ends with the separator.
        # And converts the / to the backslash separator.
        sep = '\\'
        self.assertEqual(
            sep, self.storage.clean_directory('', sep=sep))
        self.assertEqual(
            sep, self.storage.clean_directory('/', sep=sep))
        self.assertEqual(
            'base{sep}'.format(sep=sep),
            self.storage.clean_directory('base', sep=sep))
        self.assertEqual(
            'base{sep}'.format(sep=sep),
            self.storage.clean_directory('base/', sep=sep))
        self.assertEqual(
            'foo{sep}bar{sep}'.format(sep=sep),
            self.storage.clean_directory('foo/bar', sep=sep))
        self.assertEqual(
            'foo{sep}bar{sep}'.format(sep=sep),
            self.storage.clean_directory('foo/bar/', sep=sep))

    def test_clean_file(self):
        """Base storage clean file path."""
        # Always starts with the separator.
        sep = '/'

        self.assertEqual(
            '{sep}index.html'.format(sep=sep),
            self.storage.clean_file('index.html', sep=sep))
        self.assertEqual(
            '{sep}content{sep}index.html'.format(sep=sep),
            self.storage.clean_file('content/index.html', sep=sep))

        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.clean_file('', sep=sep)

        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.clean_file('/', sep=sep)

        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.clean_file('/content/', sep=sep)

    def test_clean_file_backslash(self):
        """Base storage clean file path with backslash."""
        # Always starts with the separator.
        sep = '\\'

        self.assertEqual(
            '{sep}index.html'.format(sep=sep),
            self.storage.clean_file('index.html', sep=sep))
        self.assertEqual(
            '{sep}content{sep}index.html'.format(sep=sep),
            self.storage.clean_file('content/index.html', sep=sep))

        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.clean_file('', sep=sep)

        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.clean_file('/', sep=sep)

        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.clean_file('/content/', sep=sep)

    def test_clean_path(self):
        """Base storage clean path."""
        # Always starts with the separator.
        sep = '/'

        self.assertEqual(
            '{sep}index.html'.format(sep=sep),
            self.storage.clean_file('index.html', sep=sep))
        self.assertEqual(
            '{sep}content{sep}index.html'.format(sep=sep),
            self.storage.clean_file('content/index.html', sep=sep))

    def test_clean_sep(self):
        """Base storage clean separators."""
        # And converts the / to the backslash separator.
        sep = '/'
        self.assertEqual(
            sep, self.storage.clean_sep('/', sep=sep))
        self.assertEqual(
            'base{sep}'.format(sep=sep),
            self.storage.clean_sep('base/', sep=sep))
        self.assertEqual(
            'foo{sep}bar{sep}'.format(sep=sep),
            self.storage.clean_sep('foo/bar/', sep=sep))

    def test_clean_sep_backslash(self):
        """Base storage clean separators with backslash."""
        # And converts the / to the backslash separator.
        sep = '\\'
        self.assertEqual(
            sep, self.storage.clean_sep('/', sep=sep))
        self.assertEqual(
            'base{sep}'.format(sep=sep),
            self.storage.clean_sep('base/', sep=sep))
        self.assertEqual(
            'foo{sep}bar{sep}'.format(sep=sep),
            self.storage.clean_sep('foo/bar/', sep=sep))

    def test_validate_path(self):
        """Base storage validate path."""
        # And converts the / to the backslash separator.
        sep = '/'
        self.storage.validate_path('/', sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('../', sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('/../', sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('/someting/../', sep=sep)

    def test_validate_path_backslash(self):
        """Base storage validate path with backslash."""
        # And converts the / to the backslash separator.
        sep = '\\'

        self.storage.validate_path('/', sep=sep)

        # Still doesn't work with forward slashes.
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('../', sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('/../', sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('/someting/../', sep=sep)

        # Does not let backslash relative path.
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('..{sep}'.format(sep=sep), sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path('{sep}..{sep}'.format(sep=sep), sep=sep)
        with self.assertRaises(grow_base.InvalidPathError):
            self.storage.validate_path(
                '{sep}someting{sep}..{sep}'.format(sep=sep), sep=sep)

class BaseStorageTestCase(unittest.TestCase):
    """Test the base storage."""

    def setUp(self):
        self.storage = grow_base.BaseStorage('./testdata')

    def test_copy_file(self):
        """Base storage copy file."""
        with self.assertRaises(NotImplementedError):
            self.storage.copy_file('podspec.yaml', 'podspec-copy.yaml')

    def test_copy_files(self):
        """Base storage copy files."""
        with self.assertRaises(NotImplementedError):
            self.storage.copy_files({'podspec.yaml': 'podspec-move.yaml'})

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

    def test_move_files(self):
        """Base storage move files."""
        with self.assertRaises(NotImplementedError):
            self.storage.move_files({'podspec.yaml': 'podspec-move.yaml'})

    def test_read_file(self):
        """Base storage read file."""
        with self.assertRaises(NotImplementedError):
            self.storage.read_file('podspec.yaml')

    def test_read_files(self):
        """Base storage read multiple files."""
        with self.assertRaises(NotImplementedError):
            self.storage.read_files('podspec.yaml', 'package.json')

    def test_remote_storage(self):
        """Base storage is not a remote type storage."""
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
