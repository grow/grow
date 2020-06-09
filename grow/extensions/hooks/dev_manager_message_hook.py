"""Dev manager message hook."""

from grow.extensions.hooks import base_hook


class DevManagerMessageHook(base_hook.BaseHook):
    """Hook for dev server messaging."""

    KEY = 'dev_manager_message'
    NAME = 'Dev Manager Message Handler'

    # display_func(label, message, label_color=None, message_color=None)
    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, display_func, url_base, url_root, *_args, **_kwargs):
        """Trigger the dev handler hook."""
        return previous_result
