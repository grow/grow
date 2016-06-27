from grow.pods import locales
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


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
        keys = ['$title', '$order', '$titles', 'key', 'root_key']
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

        # Currently, when requesting a document with a locale that is not
        # specified, we return a path that is unmatchable. TBD whether we want
        # to change this in a future version.
        ko_doc = self.pod.get_doc('/content/pages/contact.yaml', locale='ko')
        expected = '/ko/contact-us/'
        self.assertEqual(expected, ko_doc.url.path)
        self.assertTrue(ko_doc.exists)

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

    def test_multi_file_localization(self):
        fr_doc = self.pod.get_doc('/content/pages/intro.md', locale='fr')
        self.assertEqual(locales.Locale('fr'), fr_doc.locale)
        self.assertEqual('/content/pages/intro@fr.md', fr_doc.pod_path)
        self.assertEqual('/content/pages/intro.md', fr_doc.root_pod_path)
        self.assertIn('French About page.', fr_doc.html)
        de_doc = self.pod.get_doc('/content/pages/intro.md', locale='de')
        de_doc_from_fr_doc = fr_doc.localize('de')
        self.assertEqual(de_doc, de_doc_from_fr_doc)
        self.assertEqual('root_value', de_doc.key)
        self.assertEqual('fr_value', fr_doc.key)
        self.assertEqual('root_key_value', de_doc.root_key)
        self.assertEqual('root_key_value', fr_doc.root_key)
        # Verify '$locale' is appended.
        keys = ['$title', '$order', '$titles', 'key', 'root_key', '$locale']
        self.assertItemsEqual(keys, fr_doc.fields.keys())


if __name__ == '__main__':
    unittest.main()
