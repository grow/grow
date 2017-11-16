"""Base class for writing hooks."""

class BaseHook(object):
    """Base class for all hooks."""

    KEY = 'hook'
    NAME = 'Hook'

    def __init__(self, extension):
        self.extension = extension

    def trigger(self, previous_result, *_args, **_kwargs):
        """Trigger the hook."""
        raise NotImplementedError()
