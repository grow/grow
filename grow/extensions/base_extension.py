"""Base extension class for writing new extensions."""

from grow.common import features


class Error(Exception):
    """Base error."""
    pass


class MissingHookError(Error):
    """Missing hook error."""
    pass


class BaseExtension(object):
    """Base extension for custom extensions."""

    def __init__(self, pod, config):
        self.pod = pod
        self.config = config
        self.hooks = features.Features(default_enabled=False)

        if 'enabled' in self.config:
            for hook in self.config['enabled']:
                self.hooks.enable(hook)
        else:
            for hook in self.available_hooks:
                self.hooks.enable(hook.KEY)

        if 'disabled' in self.config:
            for hook in self.config['disabled']:
                self.hooks.disable(hook)

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return []

    def auto_hook(self, key):
        """Search for the hook in the available hooks and create."""

        # Allow for defining a *_hook method in the extension.
        hook_method = '{}_hook'.format(key)
        if hasattr(self, hook_method):
            return getattr(self, hook_method)()

        for hook in self.available_hooks:
            if hook.KEY == key:
                return hook(self)
        raise MissingHookError(
            'Hook was not found in extension: {}'.format(key))
