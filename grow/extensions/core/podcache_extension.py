"""Podcache core extension."""

from grow import extensions
from grow.extensions import hooks


class PodcacheDevFileChangeHook(hooks.BaseDevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""
        if previous_result:
            return previous_result
        return None


# pylint: disable=abstract-method
class RoutesExtension(extensions.BaseExtension):
    """Extension for handling core routes functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [PodcacheDevFileChangeHook]

    def dev_file_change_hook(self):
        """Hook handler for dev file change."""
        return PodcacheDevFileChangeHook(self)
