"""Grow locale wrapper."""

import re
import babel


class Locale(babel.Locale):
    RTL_REGEX = re.compile('^(he|ar|fa|ur)(\W|$)')
    _alias = None

    def __init__(self, language, *args, **kwargs):
        # Normalize from "de_de" to "de_DE" for case-sensitive filesystems.
        parts = language.rsplit('_', 1)
        if len(parts) > 1:
            language = '{}_{}'.format(parts[0], parts[1].upper())
        super(Locale, self).__init__(language, *args, **kwargs)

    @classmethod
    def parse(cls, *args, **kwargs):
        locale = super(Locale, cls).parse(*args, **kwargs)
        # Weak attempt to permit fuzzy locales (locales for which we still have
        # language and country information, but not a full localedata file for),
        # but disallow completely invalid locales. See note at end of file.
        if locale and locale.get_display_name() is None:
            raise ValueError(
                '{} is not a valid locale identifier'.format(args[0]))
        return locale

    def __hash__(self):
        return hash(str(self))

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
        return [cls.parse(code) for code in codes]

    @property
    def is_rtl(self):
        return Locale.RTL_REGEX.match(self.language)

    @property
    def direction(self):
        return 'rtl' if self.is_rtl else 'ltr'

    @classmethod
    def from_alias(cls, pod, alias):
        podspec = pod.get_podspec()
        config = podspec.get_config()
        if 'localization' in config and 'aliases' in config['localization']:
            aliases = config['localization']['aliases']
            for custom_locale, babel_locale in aliases.iteritems():
                if custom_locale == alias:
                    return cls.parse(babel_locale)
        return cls.parse(alias)

    def set_alias(self, podspec):
        self._alias = podspec.get_locale_alias(str(self).lower())

    @property
    def alias(self):
        return self._alias

    @alias.setter
    def alias(self, alias):
        self._alias = alias
