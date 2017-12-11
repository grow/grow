"""Tests for the translation stats."""

import unittest
from babel.messages import catalog
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
from grow.translators import translation_stats


class TranslationStatsTestCase(unittest.TestCase):

    def test_export_untranslated_catalogs(self):
        """Make sure that we can make catalogs from the untranslated strings."""
        dir_path = testing.create_test_pod_dir()
        pod = pods.Pod(dir_path, storage=storage.FileStorage)
        stats = translation_stats.TranslationStats()
        stats.tick(catalog.Message(
            'About',
            None,
        ), 'ga', 'en')
        self.assertEqual(
            {
                'ga': {
                    'About': 1,
                },
            },
            stats.untranslated)
        untranslated_catalogs = stats.export_untranslated_catalogs(pod)
        self.assertTrue('About' in untranslated_catalogs['ga'])

    def test_tick(self):
        stats = translation_stats.TranslationStats()
        stats.tick(catalog.Message(
            'About',
            'Faoi',
        ), 'ga', 'en')
        stats.tick(catalog.Message(
            'Home',
            'Baile',
        ), 'ga', 'en')
        stats.tick(catalog.Message(
            'Home',
            'Baile',
        ), 'ga', 'en')
        self.assertEqual(
            {
                'messages': {
                    'ga': {
                        'About': 1,
                        'Home': 2,
                    },
                },
                'untranslated': {},
                'untagged': {},
            },
            stats.export())

    def test_tick_none(self):
        stats = translation_stats.TranslationStats()
        stats.tick(None, 'ga', 'en')
        self.assertEqual(
            {
                'messages': {},
                'untranslated': {},
                'untagged': {},
            },
            stats.export())

    def test_count_untranslated(self):
        stats = translation_stats.TranslationStats()
        self.assertEqual(0, stats.count_untranslated)
        stats.tick(catalog.Message(
            'About',
            None,
        ), 'ga', 'en')
        self.assertEqual(1, stats.count_untranslated)
        stats.tick(catalog.Message(
            'Foo',
            None,
        ), 'ga', 'en')
        stats.tick(catalog.Message(
            'Bar',
            None,
        ), 'es', 'en')
        # Uses max across any locale. Not restricted by locale.
        self.assertEqual(3, stats.count_untranslated)

    def test_tick_untranslated(self):
        stats = translation_stats.TranslationStats()
        stats.tick(catalog.Message(
            'About',
            None,
        ), 'ga', 'en')
        self.assertEqual(
            {
                'messages': {
                    'ga': {
                        'About': 1,
                    },
                },
                'untranslated': {
                    'ga': {
                        'About': 1,
                    },
                },
                'untagged': {},
            },
            stats.export())

    def test_untagged(self):
        stats = translation_stats.TranslationStats()
        stats.add_untagged({
            '/content/pages/test.yaml': 'About',
        })
        self.assertEqual(
            {
                'messages': {},
                'untranslated': {},
                'untagged': {
                    '/content/pages/test.yaml': 'About',
                },
            },
            stats.export())

    def test_missing(self):
        stats = translation_stats.TranslationStats()
        stats.tick(catalog.Message(
            'About',
            None,
        ), 'ga', 'en')
        stats.add_untagged({
            '/content/pages/test.yaml': 'About',
        })
        self.assertEqual({
            'ga': {'About': 1}
        }, stats.missing)


if __name__ == '__main__':
    unittest.main()
