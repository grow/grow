"""Tests for Grow grow_locale."""

import unittest

from grow.cache import locale_alias_cache
from grow.translations import locale as grow_locale


class LocalesTest(unittest.TestCase):
    """Grow locale handling."""

    def test_alias(self):
        """Locales alias."""
        locale = grow_locale.Locale('en_US')
        self.assertEqual(locale.alias, None)
        locale.alias = 'en_ALL'
        self.assertEqual(locale.alias, 'en_ALL')

    def test_alias_cache(self):
        """Locales alias caching."""
        locale_cache = locale_alias_cache.LocaleAliasCache()
        locale_cache.add('en_US', 'en_ALL')
        locale = grow_locale.Locale('en_US', alias_cache=locale_cache)
        self.assertEqual(locale.alias, 'en_ALL')

    def test_eq(self):
        """Locales are equal."""
        locale = grow_locale.Locale('en_US')
        self.assertEqual(locale, 'en_US')
        self.assertEqual(locale, 'en_us')
        self.assertEqual(locale, grow_locale.Locale('en_US'))
        self.assertEqual(locale, grow_locale.Locale('en_us'))

    def test_case_sensitive(self):
        """Locales are equal."""
        locale = grow_locale.Locale('en_us')
        self.assertEqual(str(locale), 'en_US')
        locale = grow_locale.Locale('en_US')
        self.assertEqual(str(locale), 'en_US')

    def test_neq(self):
        """Locales are equal."""
        locale = grow_locale.Locale('en_US')
        self.assertNotEqual(locale, 'es_US')
        self.assertNotEqual(locale, 'fr_CA')
        self.assertNotEqual(locale, grow_locale.Locale('es_US'))
        self.assertNotEqual(locale, grow_locale.Locale('fr_CA'))

    def test_parse_codes(self):
        """Parse list of locale codes."""
        locale_list = grow_locale.Locale.parse_codes(
            ['en_US', 'fr_CA', 'ja_JP'])
        self.assertEqual('en_US', str(locale_list[0]))
        self.assertEqual('fr_CA', str(locale_list[1]))
        self.assertEqual('ja_JP', str(locale_list[2]))

    def test_repr(self):
        """Locales representation."""
        locale = grow_locale.Locale('en_US')
        self.assertEqual('<Locale: "en_US">', repr(locale))
        locale.alias = 'en_ALL'
        self.assertEqual('<Locale: "en_US" alias="en_ALL">', repr(locale))

    def test_str(self):
        """Locales string representation."""
        locale = grow_locale.Locale('en_US')
        self.assertEqual('en_US', str(locale))


if __name__ == '__main__':
    unittest.main()
