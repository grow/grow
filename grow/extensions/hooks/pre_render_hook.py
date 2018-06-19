"""Base class for the pre render hook."""

from grow.extensions.hooks import base_hook


class PreRenderHook(base_hook.BaseHook):
    """Hook for pre render."""

    KEY = 'pre_render'
    NAME = 'Pre Render'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, doc, original_body, *_args, **_kwargs):
        """Trigger the pre render hook."""
        if previous_result:
            return previous_result
        # Return None if nothing has changed.
        return None
