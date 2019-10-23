"""Tagged data management."""

import hashlib
from grow.common import decorators


class TaggedData(object):
    """Manage tagged data with built in caching."""

    def __init__(self, source, pod_path=None):
        self._source = source
        self.pod_path = pod_path

    @decorators.MemoizeProperty
    def hash(self):
        """Hash of the original value to allow for cache keys and lookups."""
        if self.source is None:
            return None
        return hashlib.sha1(self.source.encode('utf-8')).hexdigest()

    @property
    def tagged(self):
        """Parsed and still tagged from source."""
        raise NotImplementedError

    @property
    def source(self):
        """Original source string."""
        return self._source
