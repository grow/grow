"""Extension controller for working with extensions in the pod."""

from grow.extensions import hooks
from grow.extensions import hook_controller

class ExtensionController(object):
    """Controller for working with pod extensions."""

    def __init__(self, pod):
        self.pod = pod
        self._hooks = {}
        self._ext_classes = set()

        for hook in hooks.HOOKS:
            self._hooks[hook.KEY] = hook_controller.HookController(hook.KEY)

    def __len__(self):
        return len(self._ext_classes)

    def register_extensions(self, extension_classes):
        """Add new built-in extensions."""
        new_exts = []
        new_ext_classes = set(extension_classes) - self._ext_classes

        # Create a new instance of the extension for each class.
        for extension_cls in new_ext_classes:
            ext = extension_cls(self.pod, {})
            new_exts.append(ext)

        # Register the hooks with the hook controllers.
        for _, hook in self._hooks.items():
            hook.register_extensions(new_exts)

        # Track the added classes to prevent duplicate extension creation.
        self._ext_classes |= new_ext_classes

    def trigger(self, hook_key, *args, **kwargs):
        """Trigger a hook."""
        return self._hooks[hook_key].trigger(*args, **kwargs)
