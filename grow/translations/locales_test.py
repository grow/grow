"""Tests for Grow locales."""

import unittest

from grow.translations import locales


class LocalesTest(unittest.TestCase):
    """Grow locale handling."""

    def test_eq(self):
        """Locales are equal."""
        locale = locales.Locale('en_US')
        self.assertEqual(locale, 'en_US')
        self.assertEqual(locale, 'en_us')
        self.assertEqual(locale, locales.Locale('en_US'))
        self.assertEqual(locale, locales.Locale('en_us'))

    def test_case_sensitive(self):
        """Locales are equal."""
        locale = locales.Locale('en_us')
        self.assertEqual(str(locale), 'en_US')
        locale = locales.Locale('en_US')
        self.assertEqual(str(locale), 'en_US')

    def test_neq(self):
        """Locales are equal."""
        locale = locales.Locale('en_US')
        self.assertNotEqual(locale, 'es_US')
        self.assertNotEqual(locale, 'fr_CA')
        self.assertNotEqual(locale, locales.Locale('es_US'))
        self.assertNotEqual(locale, locales.Locale('fr_CA'))

    def test_parse(self):
        """Locales parsing."""
        locale = locales.Locale.parse('en_US')
        self.assertEqual('en_US', str(locale))

        locale = locales.Locale.parse('en-US', sep='-')
        self.assertEqual('en_US', str(locale))

    def test_repr(self):
        """Locales representation."""
        locale = locales.Locale('en_US')
        self.assertEqual('<Locale: "en_US">', repr(locale))

    def test_str(self):
        """Locales string representation."""
        locale = locales.Locale('en_US')
        self.assertEqual('en_US', str(locale))


if __name__ == '__main__':
    unittest.main()
