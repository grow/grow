"""Extension controller for working with extensions in the pod."""

from grow.extensions import core
from grow.extensions import extension_importer
from grow.extensions import hooks
from grow.extensions import hook_controller

class ExtensionController(object):
    """Controller for working with pod extensions."""

    def __init__(self, pod):
        self.pod = pod
        self._hooks = {}
        self._extensions = {}

        for hook in hooks.HOOKS:
            self._hooks[hook.KEY] = hook_controller.HookController(
                self.pod, hook.KEY, hook(None))

    def extension_config(self, extension_path):
        if extension_path not in self._extensions:
            return {}
        return  self._extensions[extension_path].config

    def register_builtins(self):
        """Add new built-in extensions."""
        new_extensions = []
        for extension_cls in core.EXTENSIONS:
            ext = extension_cls(self.pod, {})
            new_extensions.append(ext)

        # Register the hooks with the hook controllers.
        for _, hook in self._hooks.items():
            hook.register_extensions(new_extensions)

    def register_extensions(self, extension_configs):
        """Add new extensions to the controller."""
        new_extensions = []
        for config_item in extension_configs:
            if isinstance(config_item, str):
                extension_path = config_item
                config = {}
            else:
                extension_path = list(config_item.keys())[0]
                config = config_item[extension_path]
            cls = extension_importer.ExtensionImporter.find_extension(
                extension_path, self.pod.root)
            ext = cls(self.pod, config)
            new_extensions.append(ext)
            self._extensions[extension_path] = ext

        # Register the hooks with the hook controllers.
        for _, hook in self._hooks.items():
            hook.register_extensions(new_extensions)

    def trigger(self, hook_key, *args, **kwargs):
        """Trigger a hook."""
        return self._hooks[hook_key].trigger(*args, **kwargs)

    def update_extension_configs(self, extension_configs):
        """Update existing extensions with new configs."""
        for config_item in extension_configs:
            if isinstance(config_item, str):
                extension_path = config_item
                config = {}
            else:
                extension_path = list(config_item.keys())[0]
                config = config_item[extension_path]
            ext = self._extensions[extension_path]
            ext.config = config
