"""Tracks the rendered document information."""

import hashlib
import os


class RenderedDocument(object):
    """Keeps track of the information for the rendered document."""

    def __init__(self, path, content, tmp_dir=None):
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        self.path = path
        self.hash = hashlib.sha1(content).hexdigest()
        self.tmp_dir = tmp_dir

        if tmp_dir:
            with open(self.filename, "w") as tmp_file:
                tmp_file.write(content)
        else:
            self.content = content

    @property
    def content(self):
        """Reads the content when it needs it."""
        if not self.tmp_dir:
            return self.content

        with open(self.filename, "r") as tmp_file:
            file_contents = tmp_file.read()
            if isinstance(file_contents, unicode):
                file_contents = file_contents.encode('utf-8')
            return file_contents

    @property
    def filename(self):
        """Temp filename if has temporary dir."""
        return os.path.join(self.tmp_dir, self.hash)
