"""Pod core extension."""

from grow import extensions
from grow.extensions import hooks


class PodDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""

        if pod_path == '/{}'.format(pod.FILE_PODSPEC):
            pod.reset_yaml()

        if previous_result:
            return previous_result
        return None


# pylint: disable=abstract-method
class PodExtension(extensions.BaseExtension):
    """Extension for handling core pod functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [PodDevFileChangeHook]