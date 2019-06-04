"""Local storage for local filesystem access."""

from grow.storage import base


class LocalStorage(base.BaseStorage):
    """Access the local file system as a storage system."""

    # def copy_file(self, from_path, to_path):
    #     """Copy the file within the storage."""
    #     pass
    #
    # def delete_dir(self, file_path):
    #     """Delete a directory in the storage."""
    #     pass
    #
    # def delete_file(self, file_path):
    #     """Delete a file in the storage."""
    #     pass
    #
    # def file_exists(self, file_path):
    #     """Determine if the file exists in the storage."""
    #     pass
    #
    # def file_size(self, file_path):
    #     """Determine the filesize of the file."""
    #     pass
    #
    # def list_dir(self, file_path):
    #     """List files in a directory in the storage."""
    #     pass
    #
    # def move_file(self, from_path, to_path):
    #     """Move a file within the storage."""
    #     pass

    def read_file(self, file_path):
        """Read a file from the storage."""
        file_path = self.clean_file(file_path)
        full_path = self.expand_path(file_path)
        with open(full_path) as file_pointer:
            return file_pointer.read()

    # def read_files(self, *file_paths):
    #     """Read multiple files from the storage."""
    #     pass
    #
    # def walk(self, file_path):
    #     """Walk through the files and directories in path."""
    #     pass
    #
    # def write_file(self, file_path, content):
    #     """Write a file to the storage."""
    #     pass
