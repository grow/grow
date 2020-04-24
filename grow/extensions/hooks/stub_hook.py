"""Stub hook for fallback when older versions don't support newer hooks."""

from grow.extensions.hooks import base_hook


class StubHook(base_hook.BaseHook):
    """Hook for stubbing for newer hooks."""

    KEY = 'stub'
    NAME = 'Stub Handler'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, *_args, **_kwargs):
        """Trigger the dev handler hook."""
        return previous_result
