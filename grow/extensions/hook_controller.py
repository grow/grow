"""Hook controller for working with hooks from the extensions."""


class HookController(object):
    """Controller for working with pod extension hooks."""

    def __init__(self, pod, key, default_hook):
        self.pod = pod
        self.key = key
        self._hooks = [default_hook]

    def register_extensions(self, extensions):
        """Add new extension hooks to the controller."""
        for extension in extensions:
            if extension.hooks.is_enabled(self.key):
                hook = extension.auto_hook(self.key)
                self._hooks.append(hook)

    def trigger(self, *args, **kwargs):
        """Trigger the hook."""
        result = None
        for hook in self._hooks:
            # Hooks can determine when to be run.
            if hook.should_trigger(result, *args, **kwargs):
                timer = self.pod.profile.timer(
                    hook.__module__ + "." + hook.__class__.__name__)
                with timer:
                    result = hook.trigger(result, *args, **kwargs)
        return result
