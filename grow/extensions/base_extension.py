"""Base extension class for writing new extensions."""

from grow.common import features


class BaseExtension(object):
    """Base extension for custom extensions."""

    def __init__(self, pod, config):
        self.pod = pod
        self.config = config
        self.hooks = features.Features(default_enabled=False)

        for hook in self.available_hooks:
            self.hooks.enable(hook.KEY)

        if 'enabled' in self.config:
            for hook in self.config['enabled']:
                self.hooks.enable(hook)

        if 'disabled' in self.config:
            for hook in self.config['disabled']:
                self.hooks.disable(hook)

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return []

    def dev_handler_hook(self):
        """Hook for post rendering."""
        raise NotImplementedError()

    def post_render_hook(self):
        """Hook for post rendering."""
        raise NotImplementedError()
