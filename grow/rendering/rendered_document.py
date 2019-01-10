"""Tracks the rendered document information."""

import hashlib
import os


class RenderedDocument(object):
    """Keeps track of the information for the rendered document."""

    def __init__(self, path, content=None, tmp_dir=None):
        self.path = path
        self.tmp_dir = tmp_dir
        self.hash = None
        self._content = None

        # When doing threaded rendering the thread cannot update the timer.
        # Keep the timer with the rendered document to add to the normal
        # timers.
        self.render_timer = None
        self.write(content)

    def _has_tmp_file_path(self):
        return self.tmp_dir is not None and self.hash is not None

    def _get_tmp_file_path(self):
        """Temp filename if has temporary dir."""
        return os.path.join(self.tmp_dir, self.hash)

    @property
    def file_path(self):
        """Returns the temp file name if available."""
        if not self._has_tmp_file_path():
            return None
        return self._get_tmp_file_path()

    def read(self):
        """Reads the content when it needs it."""
        if not self._has_tmp_file_path():
            return self._content

        with open(self._get_tmp_file_path(), "r") as tmp_file:
            file_contents = tmp_file.read()
            if isinstance(file_contents, unicode):
                file_contents = file_contents.encode('utf-8')
            return file_contents

    def write(self, content):
        """Writes the content to the temp filesystem or keeps in memory."""
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        if content is None:
            self.hash = None
        else:
            self.hash = hashlib.sha1(content).hexdigest()

        if self._has_tmp_file_path():
            with open(self._get_tmp_file_path(), "w") as tmp_file:
                tmp_file.write(content)
        else:
            self._content = content
