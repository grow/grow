"""Local storage for local filesystem access."""

import errno
import os
import shutil
from grow.storage import base


class LocalStorage(base.BaseStorage):
    """Access the local file system as a storage system."""


    @staticmethod
    def make_dir(file_path):
        """Make a directory in the storage."""
        dirname = os.path.dirname(file_path)
        try:
            os.makedirs(dirname)
        except OSError as error:
            if error.errno == errno.EEXIST and os.path.isdir(dirname):
                pass
            else:
                raise

    def copy_file(self, from_path, to_path):
        """Copy the file within the storage."""
        from_path = self.clean_path(from_path)
        from_full_path = self.expand_path(from_path)
        to_path = self.clean_path(to_path)
        to_full_path = self.expand_path(to_path)
        shutil.copyfile(from_full_path, to_full_path)
        shutil.copystat(from_full_path, to_full_path)

    def copy_files(self, from_path_to_path):
        """Copy the files within the storage."""
        for from_path, to_path in from_path_to_path.items():
            self.copy_file(from_path, to_path)

    def delete_dir(self, file_path):
        """Delete a directory in the storage."""
        file_path = self.clean_path(file_path)
        file_path = self.clean_directory(file_path)
        full_path = self.expand_path(file_path)
        try:
            shutil.rmtree(full_path)
        except FileNotFoundError:
            pass

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

    def list_dir(self, file_path, recursive=False):
        """List files in a directory in the storage."""
        file_path = self.clean_path(file_path)
        file_path = self.clean_directory(file_path)
        full_path = self.expand_path(file_path)
        paths = []
        for root, _, files in os.walk(full_path, topdown=True, followlinks=True):
            for filename in files:
                path = os.path.join(root, filename)[len(full_path):]
                paths.append(path)
            if not recursive:
                return paths
        return paths

    def move_file(self, from_path, to_path):
        """Move a file within the storage."""
        from_path = self.clean_path(from_path)
        from_full_path = self.expand_path(from_path)
        to_path = self.clean_path(to_path)
        to_full_path = self.expand_path(to_path)
        os.rename(from_full_path, to_full_path)

    def move_files(self, from_path_to_path):
        """Move files within the storage."""
        for from_path, to_path in from_path_to_path.items():
            self.move_file(from_path, to_path)

    def read_file(self, file_path):
        """Read a file from the storage."""
        file_path = self.clean_file(file_path)
        full_path = self.expand_path(file_path)
        with open(full_path) as file_pointer:
            return file_pointer.read()

    def read_files(self, *file_paths):
        """Read multiple files from the storage."""
        results = {}
        for file_path in file_paths:
            file_path = self.clean_file(file_path)
            full_path = self.expand_path(file_path)
            with open(full_path) as file_pointer:
                results[file_path] = file_pointer.read()
        return results

    # def walk(self, file_path):
    #     """Walk through the files and directories in path."""
    #     pass

    def write_file(self, file_path, content):
        """Write a file to the storage."""
        file_path = self.clean_file(file_path)
        full_path = self.expand_path(file_path)
        self.make_dir(full_path)
        with open(full_path, 'w') as file_pointer:
            file_pointer.write(content)
