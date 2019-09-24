"""Base class for the pre deploy hook."""

from grow.extensions.hooks import base_hook


class PreDeployHook(base_hook.BaseHook):
    """Hook for pre deploy."""

    KEY = 'pre_deploy'
    NAME = 'Pre Deploy'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, rendered_doc, command, *_args, **_kwargs):
        """Trigger the pre deploy hook."""
        if previous_result:
            return previous_result
        # Return None if nothing has changed.
        return None
