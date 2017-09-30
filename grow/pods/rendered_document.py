"""Tracks the rendered document information."""

import hashlib

class RenderedDocument(object):
    """Keeps track of the information for the rendered document."""

    def __init__(self, path, content):
        if isinstance(content, unicode):
            content = content.encode('utf-8')

        self.path = path
        self.content = content
        self.hash = hashlib.sha1(content).hexdigest()
