"""Dev manager message hook."""

from grow.extensions.hooks import base_hook


class DevManagerMessageHook(base_hook.BaseHook):
    """Hook for dev server messaging."""

    KEY = 'dev_manager_message'
    NAME = 'Dev Manager Message Handler'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, first_column_width, url, *_args, **_kwargs):
        """Trigger the dev handler hook."""
        return previous_result
