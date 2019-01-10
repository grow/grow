"""Base Config control class."""


class BaseConfig(object):
    """Base class for identifier based configuration management."""

    def __init__(self, config=None):
        self._config = config or {}

    @staticmethod
    def _split_identifier(identifier):
        return identifier.split('.')

    def export(self):
        """Export the raw config."""
        return self._config

    def get(self, identifier, default_value=None):
        """Retrieve the identifier value in the config."""
        parts = self._split_identifier(identifier)
        item = self._config
        for part in parts:
            if part not in item:
                return default_value
            item = item[part]
        return item

    def prefixed(self, prefix):
        """Create a utility for accessing config with a common identifier prefix."""
        return BaseConfigPrefixed(self, prefix)

    def set(self, identifier, value):
        """Set the value of the identifier in the config."""
        parts = self._split_identifier(identifier)
        key = parts.pop()
        item = self._config
        for part in parts:
            if part not in item:
                item[part] = {}
            item = item[part]
        item[key] = value


class BaseConfigPrefixed(object):
    """Utility class for shortcutting common prefixes in identifiers."""

    def __init__(self, config, prefix):
        self._config = config
        self.prefix = self.normalize_prefix(prefix)

    @staticmethod
    def normalize_prefix(prefix):
        """Normalize how the prefix is formatted."""
        prefix = prefix.strip()
        if not prefix:
            return ''
        if not prefix.endswith('.'):
            prefix = '{}.'.format(prefix)
        return prefix

    def prefix_identifier(self, identifier):
        """Adds the prefix to the identifier"""
        return '{}{}'.format(self.prefix, identifier)

    def get(self, identifier, default_value=None):
        """Retrieve the identifier value in the config with prefix."""
        return self._config.get(self.prefix_identifier(identifier), default_value=default_value)

    def set(self, identifier, value):
        """Set the value of the identifier in the config with prefix."""
        return self._config.set(self.prefix_identifier(identifier), value=value)
