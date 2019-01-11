"""Features control."""

class Features(object):
    """Control features."""

    def __init__(self, enabled=None, disabled=None, default_enabled=True):
        self._enabled = set()
        self._disabled = set()
        self._config = {}
        self.default_enabled = default_enabled

        if enabled is not None:
            for feature in enabled:
                self.enable(feature)

        if disabled is not None:
            for feature in disabled:
                self.disable(feature)

    def config(self, feature):
        """Configuration for a feature."""
        return self._config.get(feature, {})

    def disable(self, feature):
        """Disable the feature."""
        self._disabled.add(feature)

    def enable(self, feature, config=None):
        """Enable the feature."""
        self._enabled.add(feature)
        self._disabled.discard(feature)
        self._config[feature] = config or {}

    def is_disabled(self, feature):
        """Determine if the feature is disabled."""
        return not self.is_enabled(feature)

    def is_enabled(self, feature):
        """Determine if the feature is enabled."""
        if feature in self._disabled:
            return False
        if feature in self._enabled:
            return True
        return self.default_enabled is True
