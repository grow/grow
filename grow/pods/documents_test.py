import os
import textwrap
import unittest

from . import documents
from . import formats
from . import locales
from . import pods
from . import routes
from . import storage
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
            'csv_data@',
            'doc_data',
            'doc_url_data',
            'foo',
            'json_data',
            'static_data',
            'static_url_data',
            'tagged_fields',
            'yaml_data',
            'yaml_data@',
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

    def test_disallow_part_with_no_locale(self):
        # Doc parts must either define $locale or $locales.
        # Add test file dynamically, otherwise it'll error when other tests run
        doc_pod_path = 'content/localized/part-with-no-locale.yaml'
        with open(os.path.join(self.pod.root, doc_pod_path), 'w') as f:
            f.write(textwrap.dedent(
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

        with self.assertRaises(formats.BadLocalesError):
            self.pod.get_doc('/' + doc_pod_path)

        # This should be fine:
        with open(os.path.join(self.pod.root, doc_pod_path), 'w') as f:
            f.write(textwrap.dedent(
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
        de_doc = self.pod.get_doc('/' + doc_pod_path, locale='de')
        fr_doc = self.pod.get_doc('/' + doc_pod_path, locale='fr')
        self.assertEqual(de_doc.fields['foo'], 'bar')
        self.assertNotIn('foo', fr_doc.fields)

    def test_dont_treat_trailing_dashes_as_a_new_part(self):
        doc_pod_path = 'content/localized/part-with-trailing-dashes.yaml'
        with open(os.path.join(self.pod.root, doc_pod_path), 'w') as f:
            f.write(textwrap.dedent(
                """\
                ---
                $localization:
                    locales:
                    - de
                root_doc_part: true
                ---
                $locale: de
                subsequent_doc_part: true
                ---
                """
            ))

        doc = self.pod.get_doc('/' + doc_pod_path)
        self.assertEqual(len(doc.format._iterate_content()), 2)

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

    def test_locale_override(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en',
                'locales': [
                    'de',
                    'fr',
                    'it',
                ]
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
            '$localization': {
                'path': '/{locale}/{base}/',
            },
        })
        pod.write_yaml('/content/pages/a.yaml', {
            '$view': '/views/base.html',
            '$view@fr': '/views/base-fr.html',
            'qaz': 'qux',
            'qaz@fr': 'qux-fr',
            'qaz@de': 'qux-de',
            'qaz@fr': 'qux-fr',
            'foo': 'bar-base',
            'foo@en': 'bar-en',
            'foo@de': 'bar-de',
            'foo@fr': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
                'nested@fr': 'nested-fr',
            },
        })
        doc = pod.get_doc('/content/pages/a.yaml')
        self.assertEqual('en', doc.locale)
        self.assertEqual('bar-en', doc.foo)
        self.assertEqual('qux', doc.qaz)
        de_doc = doc.localize('de')
        self.assertEqual('bar-de', de_doc.foo)
        self.assertEqual('/views/base.html', de_doc.view)
        self.assertEqual('nested-base', de_doc.nested['nested'])
        self.assertEqual('qux-de', de_doc.qaz)
        fr_doc = doc.localize('fr')
        self.assertEqual('bar-fr', fr_doc.foo)
        self.assertEqual('/views/base-fr.html', fr_doc.view)
        self.assertEqual('nested-fr', fr_doc.nested['nested'])
        self.assertEqual('qux-fr', fr_doc.qaz)
        it_doc = doc.localize('it')
        self.assertEqual('bar-base', it_doc.foo)
        self.assertEqual('qux', it_doc.qaz)

    def test_localized_part_overrides(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en',
                'locales': [
                    'fr',
                    'ja',
                ],
            },
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$localization': {
                'path': '/{locale}/{base}/',
            }
        })
        pod.write_file('/content/pages/page.yaml', textwrap.dedent(
            """\
            ---
            foo: bar
            ---
            $locale: en
            foo: bar-en
            ---
            $locale: fr
            foo: bar-fr
            """
        ))
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual('bar-en', doc.foo)
        fr_doc = doc.localize('fr')
        self.assertEqual('bar-fr', fr_doc.foo)
        ja_doc = doc.localize('ja')
        self.assertEqual('bar', ja_doc.foo)

    def test_localization(self):
        # Localized document.
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/_blueprint.yaml', {})
        pod.write_yaml('/content/pages/page.yaml', {
            '$path': '/{base}/',
            '$localization': {
                'path': '/{locale}/{base}/',
                'locales': [
                    'de',
                ]
            }
        })
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertIsNone(doc.default_locale)
        self.assertEqual(['de'], doc.locales)
        self.assertEqual('/{base}/', doc.path_format)
        self.assertEqual('/page/', doc.url.path)
        de_doc = doc.localize('de')
        self.assertEqual('/{locale}/{base}/', de_doc.path_format)
        self.assertEqual('/de/page/', de_doc.url.path)

        # Localized collection.
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$localization': {
                'path': '/{locale}/{base}/',
                'locales': [
                    'de',
                ],
            }
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertIsNone(doc.default_locale)
        self.assertEqual(['de'], doc.locales)
        self.assertEqual('/{base}/', doc.path_format)
        de_doc = doc.localize('de')
        self.assertEqual('/{locale}/{base}/', de_doc.path_format)
        self.assertEqual('/de/page/', de_doc.url.path)

        # Localized podspec (no $localization in blueprint or doc).
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'locales': [
                    'de',
                ],
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
        })
        collection = pod.get_collection('/content/pages/')
        self.assertEqual(['de'], collection.locales)
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual(['de'], doc.locales)

        # Localized podspec ($localization in blueprint).
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'locales': [
                    'de',
                ],
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$localization': {
                'path': '/{locale}/{base}/',
            },
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        collection = pod.get_collection('/content/pages/')
        self.assertEqual(['de'], collection.locales)
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual(['de'], doc.locales)
        self.assertEqual('/{base}/', doc.path_format)
        de_doc = doc.localize('de')
        self.assertEqual('/{locale}/{base}/', de_doc.path_format)
        self.assertEqual('/de/page/', de_doc.url.path)

        # Localized podspec ($localization in blueprint, no localized path).
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'locales': [
                    'de',
                ],
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual(['de'], doc.locales)
        self.assertEqual('/{base}/', doc.path_format)
        de_doc = doc.localize('de')
        self.assertEqual('/{base}/', de_doc.path_format)
        self.assertEqual('/page/', de_doc.url.path)

        # Override collection with "$localization:locales:[]" in doc.
        pod.write_yaml('/content/pages/page.yaml', {
            '$localization': {
                'locales': [],
            },
        })
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual([], doc.locales)

        # Override collection with "$localization:~" in doc.
        pod.write_yaml('/content/pages/page.yaml', {
            '$localization': None,
        })
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual([], doc.locales)

        # Override podspec with "$localization:locales:[]" in blueprint.
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'locales': [
                    'de',
                ],
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$localization': {
                'locales': [],
            },
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        doc = pod.get_doc('/content/pages/page.yaml')
        collection = pod.get_collection('/content/pages/')
        self.assertEqual([], collection.locales)
        self.assertEqual([], doc.locales)

        # Override locales with "$localization:~" in blueprint.
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$localization': None,
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        doc = pod.get_doc('/content/pages/page.yaml')
        collection = pod.get_collection('/content/pages/')
        self.assertEqual([], collection.locales)
        self.assertEqual([], doc.locales)

        # Override the overridden podspec.
        pod.write_yaml('/content/pages/page.yaml', {
            '$localization': {
                'locales': [
                    'de',
                    'ja',
                ],
            },
        })
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual(['de', 'ja'], doc.locales)

    def test_localization_fallback(self):
        # Verify locales aren't clobbered when no localized path is specified.
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en',
                'locales': [
                    'de',
                    'en',
                ],
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        pod.write_file('/views/base.html', '{{doc.locale}}')
        self.assertRaises(routes.DuplicatePathsError, pod.match, '/page/')

        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
            '$localization': None,
        })
        controller, params = pod.match('/page/')
        content = controller.render(params)
        self.assertEqual('en', content)

    def test_view_format(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/{base}.html',
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        doc = pod.get_doc('/content/pages/page.html')
        self.assertEqual('/views/page.html', doc.view)


if __name__ == '__main__':
    unittest.main()
