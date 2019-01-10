"""Tests for Grow locales."""

import unittest
from grow.testing import testing
from grow.translations import locales


class LocalesTest(unittest.TestCase):

    def test_eq(self):
        locale = locales.Locale('en_US')
        self.assertEqual(locale, 'en_US')
        self.assertEqual(locale, 'en_us')
        self.assertEqual(locale, locales.Locale('en_US'))
        self.assertEqual(locale, locales.Locale('en_us'))

    def test_locale_aliases(self):
        # Verify case insensitivty for locale aliases.
        pod = testing.create_test_pod()
        locale = locales.Locale('de')
        locale.set_alias(pod)
        self.assertEqual('de_alias', locale.alias)
        locale = locales.Locale('DE')
        locale.set_alias(pod)
        self.assertEqual('de_alias', locale.alias)

    def test_fuzzy_locales(self):
        locale = locales.Locale.parse('en_BD')
        self.assertEqual('en', locale.language)
        self.assertEqual('BD', locale.territory)
        self.assertEqual('English (Bangladesh)', locale.get_display_name())
        locale = locales.Locale.parse('en_INVALID')
        self.assertEqual('en', locale.language)
        self.assertEqual(None, locale.territory)
        self.assertRaises(ValueError, locales.Locale.parse, 'invalid')
        self.assertRaises(ValueError, locales.Locale.parse, 'invalid_US')


if __name__ == '__main__':
    unittest.main()
