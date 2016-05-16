import os
from textwrap import dedent
import unittest

from grow.pods import formats
from grow.pods import locales
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing


class DocumentsTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_eq(self):
        doc1 = self.pod.get_doc('/content/pages/contact.yaml')
        doc2 = self.pod.get_doc('/content/pages/contact.yaml')
        self.assertEqual(doc1, doc2)
        col = self.pod.get_collection('pages')
        for doc in col:
            if doc.pod_path == '/content/pages/contact.yaml':
                self.assertEqual(doc1, doc)
                self.assertEqual(doc2, doc)

    def test_doc_storage(self):
        # Because this test involves translation priority, ensure that we have
        # compiled the MO files before running the test.
        self.pod.catalogs.compile()

        doc = self.pod.get_doc('/content/pages/intro.md')
        self.assertEqual('About page.', doc.body)
        self.assertEqual('<p>About page.</p>', doc.html)
        keys = ['$title', '$order', '$titles']
        self.assertItemsEqual(keys, doc.fields.keys())

        doc = self.pod.get_doc('/content/pages/home.yaml')
        keys = [
            '$localization',
            '$order',
            '$path',
            '$title',
            '$view',
            'csv_data',
            'doc_data',
            'doc_url_data',
            'foo',
            'json_data',
            'static_data',
            'static_url_data',
            'tagged_fields',
            'yaml_data',
        ]
        self.assertItemsEqual(keys, doc.fields.keys())
        self.assertIsNone(doc.html)

        about = self.pod.get_doc('/content/pages/about.yaml')
        self.assertEqual(doc.doc_data, about)
        self.assertEqual(doc.doc_url_data, about.url)

        static = self.pod.get_static('/static/test.txt')
        self.assertEqual(doc.static_data, static)
        self.assertEqual(doc.static_url_data, static.url)

        default_doc = self.pod.get_doc('/content/pages/about.yaml')
        self.assertEqual('bar', default_doc.foo)

        de_doc = self.pod.get_doc('/content/pages/about.yaml', locale='de')
        self.assertEqual('baz', de_doc.foo)
        self.assertEqual('qux', de_doc.qaz)

    def test_locales(self):
        doc = self.pod.get_doc('/content/pages/contact.yaml')
        self.assertEqual(locales.Locale('de'), doc.locale)
        expected = locales.Locale.parse_codes([
            'de',
            'fr',
            'it',
        ])
        self.assertEqual(expected, doc.locales)

    def test_next_prev(self):
        collection = self.pod.get_collection('pages')
        docs = collection.list_docs()
        doc = self.pod.get_doc('/content/pages/contact.yaml')
        doc.next(docs)
        self.assertRaises(ValueError, doc.next, [1, 2, 3])
        doc.prev(docs)
        self.assertRaises(ValueError, doc.prev, [1, 2, 3])

    def test_default_locale(self):
        doc = self.pod.get_doc('/content/localized/localized.yaml', locale='de')
        self.assertEqual('/views/localized.html', doc.view)
        self.assertEqual(locales.Locale('de'), doc.locale)
        self.assertEqual('base', doc.foo)
        self.assertEqual('baz', doc.bar)

        doc = self.pod.get_doc('/content/localized/localized.yaml')
        self.assertEqual('/views/ja-specific-view.html', doc.view)
        self.assertEqual(locales.Locale('ja'), doc.locale)
        self.assertEqual(locales.Locale('ja'), doc.default_locale)
        self.assertEqual('base_ja', doc.foo)
        self.assertEqual('baz', doc.bar)

        doc = self.pod.get_doc('/content/localized/localized.yaml', locale='ja')
        self.assertEqual('/views/ja-specific-view.html', doc.view)
        self.assertEqual(locales.Locale('ja'), doc.locale)
        self.assertEqual('base_ja', doc.foo)
        self.assertEqual('baz', doc.bar)

        doc = self.pod.get_doc('/content/localized/localized.yaml', locale='fr')
        self.assertEqual('/views/localized.html', doc.view)
        self.assertEqual(locales.Locale('fr'), doc.locale)
        self.assertEqual('base', doc.foo)
        self.assertEqual('baz', doc.bar)
        self.assertEqual('/intl/fr/localized/', doc.url.path)

    def test_disallow_part_with_no_locale(self):
        # Doc parts must either define $locale or $locales.
        # Add test file dynamically, otherwise it'll error when other tests run
        doc_pod_path = 'content/localized/part-with-no-locale.yaml'
        with open(os.path.join(self.pod.root, doc_pod_path), 'w') as f:
            f.write(dedent(
                """\
                ---
                $title: Multiple Locales
                $localization:
                  path: /intl/{locale}/multiple-locales/
                  locales:
                  - de
                ---
                foo: bar
                """
            ))

        with self.assertRaises(formats.BadFormatError):
            self.pod.get_doc('/content/localized/part-with-no-locale.yaml')

        # This should be fine:
        with open(os.path.join(self.pod.root, doc_pod_path), 'w') as f:
            f.write(dedent(
                """\
                ---
                $title: Multiple Locales
                $localization:
                  path: /intl/{locale}/multiple-locales/
                  locales:
                  - de
                  - fr
                ---
                $locale: de
                foo: bar
                """
            ))
        de_doc = self.pod.get_doc('/content/localized/part-with-no-locale.yaml', locale='de')
        fr_doc = self.pod.get_doc('/content/localized/part-with-no-locale.yaml', locale='fr')
        self.assertEqual(de_doc.fields['foo'], 'bar')
        self.assertNotIn('foo', fr_doc.fields)

    def test_view_override(self):
        doc = self.pod.get_doc('/content/localized/localized-view-override.yaml')
        self.assertEqual('/views/localized.html', doc.view)
        self.assertEqual(locales.Locale.parse('en_PK'), doc.locale)

        doc = self.pod.get_doc('/content/localized/localized-view-override.yaml',
                               locale='en_PK')
        self.assertEqual('/views/localized.html', doc.view)
        self.assertEqual(locales.Locale.parse('en_PK'), doc.locale)

        doc = self.pod.get_doc('/content/localized/localized-view-override.yaml',
                               locale='tr_TR')
        self.assertEqual('/views/tr-specific-view.html', doc.view)
        self.assertEqual(locales.Locale.parse('tr_TR'), doc.locale)

    def test_exists(self):
        doc = self.pod.get_doc('/content/localized/localized.yaml')
        self.assertTrue(doc.exists)
        doc = self.pod.get_doc('/content/localized/localized.yaml', locale='ja')
        self.assertTrue(doc.exists)
        doc = self.pod.get_doc('/content/localized/localized.yaml', locale='de')
        self.assertTrue(doc.exists)
        doc = self.pod.get_doc('/content/localized/does-not-exist.yaml')
        self.assertFalse(doc.exists)

if __name__ == '__main__':
    unittest.main()
