"""Tracks the rendered document information."""

import hashlib
import os


class RenderedDocument(object):
    """Keeps track of the information for the rendered document."""

    def __init__(self, path, content=None, tmp_dir=None):
        self.path = path
        self.tmp_dir = tmp_dir
        self.hash = None

        if content:
            self.write(content)

    def _get_tmp_filename(self):
        """Temp filename if has temporary dir."""
        return os.path.join(self.tmp_dir, self.hash)

    def read(self):
        """Reads the content when it needs it."""
        if not self.tmp_dir:
            return self._content

        with open(self._get_tmp_filename(), "r") as tmp_file:
            file_contents = tmp_file.read()
            if isinstance(file_contents, unicode):
                file_contents = file_contents.encode('utf-8')
            return file_contents

    def write(self, content):
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        self.hash = hashlib.sha1(content).hexdigest()

        if self.tmp_dir:
            with open(self._get_tmp_filename(), "w") as tmp_file:
                tmp_file.write(content)
        else:
            self._content = content
