"""Storage utility for testing."""

import errno
import os
import shutil
import tempfile
from grow.storage import local as grow_local

class TestFileStorage(object):
    """Temporary file system access for testing."""

    def __init__(self):
        self.content_dir = tempfile.mkdtemp()

    def tear_down(self):
        """Tear down the storage to cleanup after tests."""
        try:
            shutil.rmtree(self.content_dir)
        except FileNotFoundError:
            pass

    def write(self, filename, content):
        """Write file for testing outside of the storage class."""

        filename = os.path.join(self.content_dir, filename)
        dirname = os.path.dirname(filename)
        try:
            os.makedirs(dirname)
        except OSError as error:
            if error.errno == errno.EEXIST and os.path.isdir(dirname):
                pass
            else:
                raise
        with open(filename, 'w') as file_pointer:
            file_pointer.write(content)
