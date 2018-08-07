"""Grow locale wrapper."""

import babel


class Locale(babel.Locale):
    """Grow locale."""

    def __init__(self, language, *args, alias_cache=None, **kwargs):
        # Normalize from "de_de" to "de_DE" for case-sensitive filesystems.
        parts = language.rsplit('_', 1)
        if len(parts) > 1:
            language = '{}_{}'.format(parts[0], parts[1].upper())
        super(Locale, self).__init__(language, *args, **kwargs)

        # Use the alias_cache to determine if this locale has an alias.
        self.alias = None
        if alias_cache:
            self.alias = alias_cache.get_alias(str(self))

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self).lower() == other.lower()
        return super(Locale, self).__eq__(other)

    def __repr__(self):
        return '<Locale: "{}">'.format(str(self))

    @classmethod
    def parse_codes(cls, codes):
        """Parse a list of codes into a list of locale objects."""
        return [cls.parse(code) for code in codes]
