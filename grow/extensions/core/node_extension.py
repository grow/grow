"""Node core extension."""

from grow import extensions
from grow.extensions import hooks


class NodeDevFileChangeHook(hooks.DevFileChangeHook):
    """Handle the dev file change hook."""

    # pylint: disable=arguments-differ
    def trigger(self, previous_result, pod_path, *_args, **_kwargs):
        """Trigger the file change hook."""
        if pod_path == '/package.json':
            self.pod.logger.info(
                'package.json has changed. Run `grow install` to install updates.')

        if previous_result:
            return previous_result
        return None


# pylint: disable=abstract-method
class NodeExtension(extensions.BaseExtension):
    """Extension for handling core node functionality."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [NodeDevFileChangeHook]
