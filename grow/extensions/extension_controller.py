"""Extension controller for working with extensions in the pod."""

from grow.common import extensions as common_extensions
from grow.extensions import core
from grow.extensions import hooks
from grow.extensions import hook_controller

class ExtensionController(object):
    """Controller for working with pod extensions."""

    def __init__(self, pod):
        self.pod = pod
        self._hooks = {}

        for hook in hooks.HOOKS:
            self._hooks[hook.KEY] = hook_controller.HookController(
                self.pod, hook.KEY, hook(None))

    def register_builtins(self):
        """Add new built-in extensions."""
        new_extensions = []
        for extension_cls in core.EXTENSIONS:
            ext = extension_cls(self.pod, {})
            new_extensions.append(ext)

        # Register the hooks with the hook controllers.
        for _, hook in self._hooks.iteritems():
            hook.register_extensions(new_extensions)

    def register_extensions(self, extension_configs):
        """Add new extensions to the controller."""
        new_extensions = []
        for config_item in extension_configs:
            if isinstance(config_item, basestring):
                extension_path = config_item
                config = {}
            else:
                extension_path = config_item.keys()[0]
                config = config_item[extension_path]
            cls = common_extensions.import_extension(extension_path, [self.pod.root])
            ext = cls(self.pod, config)
            new_extensions.append(ext)

        # Register the hooks with the hook controllers.
        for _, hook in self._hooks.iteritems():
            hook.register_extensions(new_extensions)

    def trigger(self, hook_key, *args, **kwargs):
        """Trigger a hook."""
        return self._hooks[hook_key].trigger(*args, **kwargs)
