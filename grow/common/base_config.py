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
