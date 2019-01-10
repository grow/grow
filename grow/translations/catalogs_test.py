"""Tests for translation catalogs."""

import os
import unittest
from grow.pods import pods
from grow import storage
from grow.testing import testing
from grow.translations import catalogs


class CatalogTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_to_message(self):
        de_catalog = self.pod.catalogs.get('de')
        de_catalog.to_message()

    def test_init(self):
        de_catalog = self.pod.catalogs.get('de')
        de_catalog.init('translations/messages.pot')

    def test_update(self):
        de_catalog = self.pod.catalogs.get('de')
        de_catalog.update()

    def test_exists(self):
        de_catalog = self.pod.catalogs.get('de')
        self.assertTrue(de_catalog.exists)
        da_catalog = self.pod.catalogs.get('da')
        self.assertFalse(da_catalog.exists)

    def test_compile(self):
        de_catalog = self.pod.catalogs.get('de')
        de_catalog.compile()

    def test_in(self):
        de_catalog = self.pod.catalogs.get('de')
        self.assertIn('AboutDE', de_catalog)
        self.assertEqual(21, len(de_catalog))

    def test_save(self):
        it_catalog = self.pod.catalogs.get('it')
        self.assertNotIn('foo', it_catalog)
        it_catalog.add('foo', 'bar')
        it_catalog.save()

        it_catalog = self.pod.catalogs.get('it')
        self.assertIn('foo', it_catalog)
        it_catalog.delete('foo')
        it_catalog.save()

        it_catalog = self.pod.catalogs.get('it')
        self.assertNotIn('foo', it_catalog)

    def test_list_untranslated(self):
        de_catalog = self.pod.catalogs.get('de')
        untranslated = de_catalog.list_untranslated()
        self.assertEqual(3, len(untranslated))
        fr_catalog = self.pod.catalogs.get('fr')
        untranslated = fr_catalog.list_untranslated()
        self.assertEqual(14, len(untranslated))

    def test_machine_translate(self):
        # Skip this test in Travis to avoid Google Translate 503s.
        if os.getenv('TRAVIS'):
            return
        de_catalog = self.pod.catalogs.get('de')
        de_catalog.machine_translate()

    def test__message_in_paths(self):
        class DummyMessage(object):
            def __init__(self, locations):
                self.locations = [(location, 0) for location in locations]
        message = DummyMessage([
            '/content/pages/foo.yaml',
            '/content/pages/bar.yaml',
        ])

        paths = [
            '/content/pages/foo*',
            '/content/pages/foo.yaml',
            '/content/*/foo.yaml',
            '/content/*/*.yaml',
            '/content/pages/bar*',
            '/content/pages/bar.yaml',
            '/content/*/bar.yaml',
        ]
        for path in paths:
            self.assertTrue(catalogs.Catalog._message_in_paths(message, [path]))

        paths = [
            'content/pages/foo*',
            'content/pages/foo.yaml',
            'content/*/foo.yaml',
            'content/*/*.yaml',
            'content/pages/bar*',
            'content/pages/bar.yaml',
            'content/*/bar.yaml',
        ]
        for path in paths:
            self.assertTrue(catalogs.Catalog._message_in_paths(message, [path]))

        paths = [
            'content/pages/qaz*',
            'content/pages/qaz.yaml',
            'content/*/qaz.yaml',
        ]
        for path in paths:
            self.assertFalse(
                    catalogs.Catalog._message_in_paths(message, [path]))


if __name__ == '__main__':
    unittest.main()
