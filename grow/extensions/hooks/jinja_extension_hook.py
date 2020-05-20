"""Base class for the jinja extension hook."""

from grow.extensions.hooks import base_hook


class JinjaExtensionHook(base_hook.BaseHook):
    """Hook for jinja extension."""

    KEY = 'jinja_extensions'
    NAME = 'Jinja Extensions'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, *_args, **_kwargs):
        """Trigger the jinja extension hook."""
        if previous_result:
            return previous_result
        return []
