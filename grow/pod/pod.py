"""Grow pod container class."""

from grow.common import logger as grow_logger
from grow.performance import profile
from grow.storage import storage


class Pod(grow_logger.Logger, profile.Profiler, storage.Storager):
    """Grow pod container."""

    def __init__(self, root_path, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.root_path = root_path
