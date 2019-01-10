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

    # pylint:disable=no-self-use, unused-argument
    def should_trigger(self, previous_result, *_args, **_kwargs):
        """Determine if the hook should trigger."""
        return True

    def trigger(self, previous_result, *_args, **_kwargs):
        """Trigger the hook."""
        raise NotImplementedError()
