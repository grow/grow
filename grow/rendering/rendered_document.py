"""Tracks the rendered document information."""

import hashlib
import os


class RenderedDocument(object):
    """Keeps track of the information for the rendered document."""

    def __init__(self, path, content=None, tmp_dir=None):
        print 'rendered'
        print content
        print tmp_dir
        self.path = path
        self.tmp_dir = tmp_dir
        self.hash = None
        self._content = None

        # When doing threaded rendering the thread cannot update the timer.
        # Keep the timer with the rendered document to add to the normal timers.
        self.render_timer = None

        if content:
            self.write(content)

    def _get_tmp_file_path(self):
        """Temp filename if has temporary dir."""
        return os.path.join(self.tmp_dir, self.hash)

    @property
    def file_path(self):
        """Returns the temp file name if available."""
        if not self.tmp_dir:
            return None
        return self._get_tmp_file_path()

    def read(self):
        """Reads the content when it needs it."""
        if not self.tmp_dir:
            return self._content

        with open(self._get_tmp_file_path(), "r") as tmp_file:
            file_contents = tmp_file.read()
            if isinstance(file_contents, unicode):
                file_contents = file_contents.encode('utf-8')
            return file_contents

    def write(self, content):
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        self.hash = hashlib.sha1(content).hexdigest()

        if self.tmp_dir:
            with open(self._get_tmp_file_path(), "w") as tmp_file:
                tmp_file.write(content)
        else:
            self._content = content
