"""Dev file change hook."""

from grow.extensions.hooks import base_hook


class DevFileChangeHook(base_hook.BaseHook):
    """Hook for dev file change."""

    KEY = 'dev_file_change'
    NAME = 'Dev File Change'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, pod_path, *_args, **_kwargs):
        """Trigger the pre render hook."""
        return previous_result
