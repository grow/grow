"""Grow pod container class."""

from grow.common import logger as grow_logger
from grow.performance import profile


class Pod(object):
    """Grow pod container."""

    def __init__(self, root_path, logger=None, profiler=None):
        self.root_path = root_path
        self.logger = logger or grow_logger.LOGGER
        self.profiler = profiler or profile.Profile()
