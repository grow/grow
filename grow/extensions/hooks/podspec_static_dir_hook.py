"""Base class for the podspec static_dir hook."""

from grow.extensions.hooks import base_hook


class PodspecStaticDirHook(base_hook.BaseHook):
    """Hook for podspec static_dir."""

    KEY = 'static_dir'
    NAME = 'Podspec Static Dir'

    # pylint: disable=arguments-differ,unused-argument
    def trigger(self, previous_result, *_args, **_kwargs):
        """Trigger the podspec static_dir hook."""
        if previous_result:
            return previous_result
        return []
