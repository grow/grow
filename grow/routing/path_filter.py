"""Filter paths to control ignores and includes by path."""

import re


DEFAULT_IGNORED = [
    re.compile(r'^.*/\.[^/]*$'),  # Dot files.
]
DEFAULT_INCLUDED = []


class PathFilter(object):
    """Filter for testing paths against a set of filter criteria."""

    def __init__(self, ignored=None, included=None):
        self._ignored = []
        self._included = []

        if ignored:
            for item in ignored:
                self.add_ignored(item)

        if included:
            for item in included:
                self.add_included(item)

    def _is_ignored(self, path):
        """Test for ignored pattern match."""
        for pattern in self.ignored:
            if pattern.search(path):
                return True
        return False

    def _is_included(self, path):
        """Test for include pattern match."""
        for pattern in self.included:
            if pattern.search(path):
                return True
        return False

    @property
    def ignored(self):
        """All ignored patterns."""
        if not self._ignored and DEFAULT_IGNORED:
            self._ignored = DEFAULT_IGNORED
        for item in self._ignored:
            yield item

    @property
    def included(self):
        """All included patterns."""
        if not self._included and DEFAULT_INCLUDED:
            self._included = DEFAULT_INCLUDED
        for item in self._included:
            yield item

    def add_ignored(self, raw_pattern):
        """Add a new ignored pattern."""
        self._ignored.append(re.compile(raw_pattern))

    def add_included(self, raw_pattern):
        """Add a new included pattern."""
        self._included.append(re.compile(raw_pattern))

    def is_valid(self, path):
        """Tests if the path is valid according to the known filters."""
        if self._is_ignored(path):
            # Includes override an ignores.
            return self._is_included(path)
        return True
