"""Base class for the router add hook."""

from grow.extensions.hooks import base_hook


class RouterAddHook(base_hook.BaseHook):
    """Hook for router add."""

    KEY = 'router_add'
    NAME = 'Router Add'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, router, *_args, **_kwargs):
        """Trigger the router add hook."""
        if previous_result:
            return previous_result
        return None
