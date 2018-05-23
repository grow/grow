"""Base class for writing hooks."""

class BaseHook(object):
    """Base class for all hooks."""

    KEY = 'hook'
    NAME = 'Hook'

    def __init__(self, extension):
        self.extension = extension

    @property
    def pod(self):
        """Reference to the pod."""
        return self.extension.pod

    def trigger(self, previous_result, *_args, **_kwargs):
        """Trigger the hook."""
        raise NotImplementedError()
