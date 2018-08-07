"""Tests for the locale alias cache."""

import unittest
from . import locale_alias_cache


class LocaleAliasCacheTestCase(unittest.TestCase):
    """Tests for the locale alias cache."""

    def setUp(self):
        self.test_cache = locale_alias_cache.LocaleAliasCache()

    def test_add(self):
        """Adding to the cache works."""
        self.test_cache.add('en_US', 'en_ALL')
        self.assertEqual({
            'en_US': 'en_ALL',
        }, self.test_cache.export())

    def test_add_all(self):
        """Adding multiple to the cache works."""
        self.test_cache.add_all({
            'en_US': 'en_ALL',
            'es_US': 'es_ALL',
        })
        self.assertEqual('en_ALL', self.test_cache.alias_from_locale('en_US'))
        self.assertEqual('es_ALL', self.test_cache.alias_from_locale('es_US'))

    def test_alias_from_locale(self):
        """Adding to the cache works."""
        self.test_cache.add('en_US', 'en_ALL')
        self.assertEqual('en_ALL', self.test_cache.alias_from_locale('en_US'))
        # Fall back to the identifier if there is no alias.
        self.assertEqual('en_CA', self.test_cache.alias_from_locale('en_CA'))

    def test_remove(self):
        """Removing from the cache works."""
        self.test_cache.add('en_US', 'en_ALL')
        self.assertEqual('en_ALL', self.test_cache.alias_from_locale('en_US'))
        self.assertEqual('en_US', self.test_cache.locale_from_alias('en_ALL'))

        self.test_cache.remove('en_US')
        self.assertEqual('en_US', self.test_cache.alias_from_locale('en_US'))
        self.assertEqual(None, self.test_cache.locale_from_alias('en_ALL'))

    def test_reset(self):
        """Resetting the cache works."""
        self.test_cache.add('en_US', 'en_ALL')
        self.assertEqual('en_ALL', self.test_cache.alias_from_locale('en_US'))
        self.assertEqual('en_US', self.test_cache.locale_from_alias('en_ALL'))

        self.test_cache.reset()
        self.assertEqual('en_US', self.test_cache.alias_from_locale('en_US'))
        self.assertEqual(None, self.test_cache.locale_from_alias('en_ALL'))


if __name__ == '__main__':
    unittest.main()
