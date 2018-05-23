"""Dev handler hook."""

from grow.extensions.hooks import base_hook


class DevHandlerHook(base_hook.BaseHook):
    """Hook for dev server handlers."""

    KEY = 'dev_handler'
    NAME = 'Dev Server Handler'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, routes, *_args, **_kwargs):
        """Trigger the dev handler hook."""
        return previous_result
