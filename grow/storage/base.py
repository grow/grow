"""Base storage for file access."""


class Error(Exception):
    """Base Storage error."""
    pass


class InvalidPathError(Exception):
    """Base Storage file path error."""
    pass


class BaseStorage(object):
    """Access to a storage system for file storage."""

    IS_REMOTE_STORAGE = False

    def __init__(self, root_dir, sep='/'):
        self.sep = sep
        # Root directory should not have the trailing separator.
        self.root_dir = self.clean_directory(root_dir).rstrip(self.sep)

    @classmethod
    def clean_directory(cls, path, sep='/'):
        """Clean up a directory path."""
        path = cls.clean_sep(path, sep=sep)
        if not path.endswith(sep):
            path = '{}{}'.format(path, sep)
        return path

    @classmethod
    def clean_file(cls, path, sep='/'):
        """Clean up a file path."""
        path = cls.clean_sep(path, sep=sep)
        path = cls.clean_path(path, sep=sep)
        if path.endswith(sep):
            raise InvalidPathError(
                'Directories cannot be used as file path: {}'.format(path))
        return path

    @classmethod
    def clean_path(cls, path, sep='/'):
        """Clean up a pod path."""
        if not path.startswith(sep):
            path = '{}{}'.format(sep, path)
        return path

    @staticmethod
    def clean_sep(path, sep='/'):
        """Clean up a file path."""
        if sep != '/':
            path = path.replace('/', sep)
        return path

    @staticmethod
    def validate_path(path, sep='/'):
        """Validate that a path is valid."""
        # Cannot use relative paths for paths.
        if '..{sep}'.format(sep=sep) in path or '../' in path:
            raise InvalidPathError(
                'Unable to use relative paths to reference files.')

    def copy_file(self, from_path, to_path):
        """Copy the file within the storage."""
        raise NotImplementedError

    def copy_files(self, from_path_to_path):
        """Copy the files within the storage."""
        raise NotImplementedError

    def delete_dir(self, file_path):
        """Delete a directory in the storage."""
        raise NotImplementedError

    def delete_file(self, file_path):
        """Delete a file in the storage."""
        raise NotImplementedError

    def expand_path(self, path):
        """Expand a path to the full storage path."""
        return '{}{}'.format(self.root_dir, path)

    def expand_and_validate_path(self, path, sep='/'):
        """Expand a path to the full storage path and validate it."""
        path = self.expand_path(path)
        self.validate_path(path, sep=sep)
        return path

    def file_exists(self, file_path):
        """Determine if the file exists in the storage."""
        raise NotImplementedError

    def file_size(self, file_path):
        """Determine the filesize of the file."""
        raise NotImplementedError

    def list_dir(self, file_path, recursive=False):
        """List files in a directory in the storage."""
        raise NotImplementedError

    def move_file(self, from_path, to_path):
        """Move a file within the storage."""
        raise NotImplementedError

    def move_files(self, from_path_to_path):
        """Move files within the storage."""
        raise NotImplementedError

    def read_file(self, file_path):
        """Read a file from the storage."""
        raise NotImplementedError

    def read_files(self, *file_paths):
        """Read multiple files from the storage."""
        raise NotImplementedError

    def walk(self, file_path):
        """Walk through the files and directories in path."""
        raise NotImplementedError

    def write_file(self, file_path, content):
        """Write a file to the storage."""
        raise NotImplementedError
