"""Structured result from a grow command."""

from grow.performance import profile


# pylint: disable=too-few-public-methods
class CommandResult(object):
    """Structured result from a grow command."""

    def __init__(self, pod=None, profiler=None):
        self.pod = pod
        self.profiler = profiler or profile.Profile()
