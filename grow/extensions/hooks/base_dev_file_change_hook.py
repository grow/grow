"""Base class for the dev file change hook."""

from grow.extensions.hooks import base_hook


class BaseDevFileChangeHook(base_hook.BaseHook):
    """Base hook for dev file change."""

    KEY = 'dev_file_change'
    NAME = 'Dev File Change'

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, _pod, _pod_path, *_args, **_kwargs):
        """Trigger the pre render hook."""
        if previous_result:
            return previous_result
        return None
