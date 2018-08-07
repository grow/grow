"""Grow locale wrapper."""

import babel


class Locale(babel.Locale):
    """Grow locale."""

    def __init__(self, language, *args, **kwargs):
        self._alias = None

        # Normalize from "de_de" to "de_DE" for case-sensitive filesystems.
        parts = language.rsplit('_', 1)
        if len(parts) > 1:
            language = '{}_{}'.format(parts[0], parts[1].upper())
        super(Locale, self).__init__(language, *args, **kwargs)

    def __eq__(self, other):
        if isinstance(other, str):
            return str(self).lower() == other.lower()
        return super(Locale, self).__eq__(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<Locale: "{}">'.format(str(self))

    @classmethod
    def parse_codes(cls, codes):
        """Parse a list of codes into a list of locale objects."""
        return [cls.parse(code) for code in codes]

    @property
    def alias(self):
        """Alias for the locale if known."""
        return self._alias

    @alias.setter
    def alias(self, alias):
        self._alias = alias
