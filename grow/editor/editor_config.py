"""Editor configuration for the GUI editor."""


class EditorConfig(object):
    """Configuration object for controlling the editor."""

    def __init__(self, config=None):
        config = config or {}
        self.fields = config.get('fields', [])
        self.partials = config.get('partials', [])

    def export(self):
        """Export the config to an object."""

        return {
            'fields': self.fields,
            'partials': self.partials,
        }
