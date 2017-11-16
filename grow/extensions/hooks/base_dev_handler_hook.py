"""Base class for the dev handler hook."""

from grow.extensions.hooks import base_hook


class BaseDevHandlerHook(base_hook.BaseHook):
    """Base hook for dev server handlers."""

    KEY = 'dev_handler'
    NAME = 'Dev Server Handler'

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod, routes, debug=False, *_args, **_kwargs):
        """Trigger the dev handler hook."""
        raise NotImplementedError()
