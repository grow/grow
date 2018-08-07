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

    def test_neq(self):
        """Locales are equal."""
        locale = locales.Locale('en_US')
        self.assertNotEqual(locale, 'es_US')
        self.assertNotEqual(locale, 'fr_CA')
        self.assertNotEqual(locale, locales.Locale('es_US'))
        self.assertNotEqual(locale, locales.Locale('fr_CA'))


if __name__ == '__main__':
    unittest.main()
