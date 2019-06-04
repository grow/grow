"""Base storage for file access."""


class BaseStorage(object):
    """Access to a storage system for file storage."""

    IS_REMOTE_STORAGE = False

    def copy_file(self, from_path, to_path):
        """Copy the file within the storage."""
        raise NotImplementedError

    def delete_dir(self, file_path):
        """Delete a directory in the storage."""
        raise NotImplementedError

    def delete_file(self, file_path):
        """Delete a file in the storage."""
        raise NotImplementedError

    def file_exists(self, file_path):
        """Determine if the file exists in the storage."""
        raise NotImplementedError

    def file_size(self, file_path):
        """Determine the filesize of the file."""
        raise NotImplementedError

    def list_dir(self, file_path):
        """List files in a directory in the storage."""
        raise NotImplementedError

    def move_file(self, from_path, to_path):
        """Move a file within the storage."""
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
