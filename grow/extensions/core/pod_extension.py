"""Pod core extension."""

from grow import extensions
from grow.extensions import hooks


class PodDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""
        if pod_path == '/{}'.format(self.pod.FILE_PODSPEC):
            self.pod.reset_yaml()
        if pod_path == '/{}'.format(self.pod.FILE_EXTENSIONS):
            self.pod.logger.info(
                '{} has changed. Run `grow install` to install updates.'.format(
                    self.pod.FILE_EXTENSIONS))

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
