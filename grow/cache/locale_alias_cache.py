"""Cache for working with locale aliases based on a locale identifiers."""

class LocaleAliasCache(object):
    """Simple cache for locale aliases."""

    def __init__(self):
        self.reset()

    def add(self, identifier, value):
        """Add a value to the cache by identifier."""
        self._locales_to_alias[identifier] = value
        self._alias_to_locale[value] = identifier

    def add_all(self, identifier_to_alias):
        """Add a multiple values to the cache by identifiers."""
        for identifier, value in identifier_to_alias.items():
            self._locales_to_alias[identifier] = value
            self._alias_to_locale[value] = identifier

    def alias_from_locale(self, identifier):
        """Retrieve an alias by identifier."""
        return self._locales_to_alias.get(identifier, identifier)

    def export(self):
        """Exports all the alias cache data."""
        return self._locales_to_alias

    def locale_from_alias(self, alias):
        """Retrieve a locale by alias or None."""
        return self._alias_to_locale.get(alias, None)

    def remove(self, identifier):
        """Remove an alias by identifier."""
        alias = self._locales_to_alias.pop(identifier, None)
        if alias:
            self._alias_to_locale.pop(alias)
            return alias

    def reset(self):
        """Resets the internal cache reference."""
        self._locales_to_alias = {}
        self._alias_to_locale = {}
