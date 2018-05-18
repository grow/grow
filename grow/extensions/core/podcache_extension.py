"""Podcache core extension."""

from grow import extensions
from grow.extensions import hooks


class PodcacheDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""

        # Remove any raw file in the cache.
        pod.podcache.file_cache.remove(pod_path)

        if previous_result:
            return previous_result
        return None


# pylint: disable=abstract-method
class PodcacheExtension(extensions.BaseExtension):
    """Extension for handling core routes functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [PodcacheDevFileChangeHook]

    def dev_file_change_hook(self):
        """Hook handler for dev file change."""
        return PodcacheDevFileChangeHook(self)
