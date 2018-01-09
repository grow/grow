"""Tests for documents."""

import textwrap
import unittest
from grow.common import utils
from grow.testing import testing
from grow.documents import document
from grow.translations import locales
from grow.pods import pods
from grow.pods import routes
from grow import storage


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

        doc1 = self.pod.get_doc('/content/pages/about.yaml')
        doc2 = self.pod.get_doc('/content/pages/about@de.yaml')
        self.assertEqual(doc1, doc2)

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

    def test_clean_localized_path(self):
        input = '/content/pages/about.yaml'
        expected = '/content/pages/about.yaml'
        self.assertEquals(expected, document.Document.clean_localized_path(
            input, None))

        input = '/content/pages/about@de.yaml'
        expected = '/content/pages/about@de.yaml'
        self.assertEquals(expected, document.Document.clean_localized_path(
            input, 'de'))

        input = '/content/pages/about@de.yaml'
        expected = '/content/pages/about.yaml'
        self.assertEquals(expected, document.Document.clean_localized_path(
            input, 'en'))

    def test_collection_base_path(self):
        about_doc = self.pod.get_doc('/content/pages/about.yaml')
        self.assertEquals('/', about_doc.collection_base_path)

        about_doc = self.pod.get_doc('/content/pages/sub/about.yaml')
        self.assertEquals('/sub/', about_doc.collection_base_path)

        about_doc = self.pod.get_doc('/content/pages/sub/foo/about.yaml')
        self.assertEquals('/sub/foo/', about_doc.collection_base_path)

    def test_collection_path(self):
        about_doc = self.pod.get_doc('/content/pages/about.yaml')
        self.assertEquals('/about.yaml', about_doc.collection_path)

        about_doc = self.pod.get_doc('/content/pages/sub/about.yaml')
        self.assertEquals('/sub/about.yaml', about_doc.collection_path)

        about_doc = self.pod.get_doc('/content/pages/sub/foo/about.yaml')
        self.assertEquals('/sub/foo/about.yaml', about_doc.collection_path)

    def test_get_serving_path(self):
        about_doc = self.pod.get_doc('/content/pages/about.yaml')
        self.assertEquals('/about/', about_doc.get_serving_path())

        de_doc = self.pod.get_doc('/content/pages/about.yaml', locale='de')
        self.assertEquals('/de_alias/about/', de_doc.get_serving_path())

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

    def test_parse_localized_path(self):
        path = '/content/pages/file@en_us.ext'
        expected = ('/content/pages/file.ext', 'en_us')
        self.assertEqual(
            expected, document.Document.parse_localized_path(path))
        path = '/content/pages/file@en.ext'
        expected = ('/content/pages/file.ext', 'en')
        self.assertEqual(
            expected, document.Document.parse_localized_path(path))
        path = '/content/pages/file.ext'
        expected = ('/content/pages/file.ext', None)
        self.assertEqual(
            expected, document.Document.parse_localized_path(path))

    def test_localize_path(self):
        path = '/content/pages/file.ext'
        locale = 'locale'
        expected = '/content/pages/file@locale.ext'
        self.assertEqual(
            expected, document.Document.localize_path(path, locale=locale))

        # No Locale
        path = '/content/pages/file.ext'
        locale = None
        expected = '/content/pages/file.ext'
        self.assertEqual(
            expected, document.Document.localize_path(path, locale=locale))

        # Existing Locale
        path = '/content/pages/file@locale.ext'
        locale = 'elacol'
        expected = '/content/pages/file@elacol.ext'
        self.assertEqual(
            expected, document.Document.localize_path(path, locale=locale))

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
        self.assertEqual('/views/ja-specific-view.html', doc.view)
        self.assertEqual(locales.Locale('de'), doc.locale)
        self.assertEqual('base_ja', doc.foo)
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
        self.assertEqual('/views/ja-specific-view.html', doc.view)
        self.assertEqual(locales.Locale('fr'), doc.locale)
        self.assertEqual('base_ja', doc.foo)
        self.assertEqual('baz', doc.bar)
        self.assertEqual('/intl/fr/localized/', doc.url.path)

        doc = self.pod.get_doc('/content/localized/localized.yaml', locale='en')
        self.assertEqual('/views/localized.html', doc.view)
        self.assertEqual(locales.Locale('en'), doc.locale)
        self.assertEqual('base', doc.foo)
        self.assertEqual('baz', doc.bar)
        self.assertEqual('/intl/en/localized/', doc.url.path)

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
        keys = ['$title', '$order', '$titles', 'key', 'root_key']
        self.assertItemsEqual(keys, fr_doc.fields.keys())

    def test_default_locale_override(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en',
                'locales': [
                    'en',
                    'de',
                    'it',
                ]
            }
        })
        pod.write_file('/views/base.html', '{{doc.foo}}')
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
            '$localization': {
                'path': '/{locale}/{base}/',
            },
        })
        pod.write_yaml('/content/pages/page.yaml', {
            '$localization': {
                'default_locale': 'de',
            },
            'foo': 'foo-base',
            'foo@de': 'foo-de',
        })
        pod.write_yaml('/content/pages/page2.yaml', {
            'foo': 'foo-base',
            'foo@de': 'foo-de',
        })
        # Verify ability to override using the default locale.
        controller, params = pod.match('/page/')
        content = controller.render(params)
        self.assertEqual('foo-de', content)
        controller, params = pod.match('/en/page/')
        content = controller.render(params)
        self.assertEqual('foo-base', content)
        # Verify default behavior otherwise.
        controller, params = pod.match('/page2/')
        content = controller.render(params)
        self.assertEqual('foo-base', content)
        controller, params = pod.match('/de/page2/')
        content = controller.render(params)
        self.assertEqual('foo-de', content)

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
        pod.write_yaml('/content/pages/page.yaml', {})
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
        pod.routes.reset_cache()
        controller, params = pod.match('/page/')
        content = controller.render(params)
        self.assertEqual('en', content)

        # Verify paths aren't clobbered by the default locale.
        pod.write_yaml('/content/pages/page.yaml', {
            '$path': '/{locale}/{base}/',
            '$view': '/views/base.html',
            '$localization': {
                'default_locale': 'de',
                'path': '/{locale}/{base}/',
                'locales': [
                    'en',
                    'de',
                ],
            },
        })
        pod.podcache.reset()
        pod.routes.reset_cache()
        controller, params = pod.match('/de/page/')
        content = controller.render(params)
        self.assertEqual('de', content)
        paths = pod.routes.list_concrete_paths()
        expected = ['/en/page/', '/de/page/']
        self.assertEqual(expected, paths)

    def test_view_format(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/{base}.html',
        })
        pod.write_yaml('/content/pages/page.yaml', {})
        doc = pod.get_doc('/content/pages/page.yaml')
        self.assertEqual('/views/page.html', doc.view)

    def test_recursive_yaml(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/{base}.html',
            '$localization': {
                'default_locale': 'en',
                'locales': ['de', 'en'],
            }
        })
        pod.write_file('/content/pages/foo.yaml', textwrap.dedent(
            """\
            bar: !g.doc /content/pages/bar.yaml
            """))
        pod.write_file('/content/pages/bar.yaml', textwrap.dedent(
            """\
            foo: !g.doc /content/pages/foo.yaml
            """))
        foo_doc = pod.get_doc('/content/pages/foo.yaml', locale='de')
        bar_doc = pod.get_doc('/content/pages/bar.yaml', locale='de')
        self.assertEqual(bar_doc, foo_doc.bar)
        self.assertEqual(bar_doc, foo_doc.bar.foo.bar)
        self.assertEqual('de', foo_doc.bar.locale)
        self.assertEqual(foo_doc, bar_doc.foo)
        self.assertEqual(foo_doc, bar_doc.foo.bar.foo)
        self.assertEqual('de', bar_doc.foo.locale)
        foo_doc = pod.get_doc('/content/pages/foo.yaml', locale='en')
        bar_doc = pod.get_doc('/content/pages/bar.yaml', locale='en')
        self.assertEqual(bar_doc, foo_doc.bar)
        self.assertEqual(bar_doc, foo_doc.bar.foo.bar)
        self.assertEqual('en', foo_doc.bar.locale)
        self.assertEqual(foo_doc, bar_doc.foo)
        self.assertEqual(foo_doc, bar_doc.foo.bar.foo)
        self.assertEqual('en', bar_doc.foo.locale)

    def test_locale_paths(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_file('/content/pages/foo@en_us.yaml', '')
        pod.write_file('/content/pages/foo@en.yaml', '')
        pod.write_file('/content/pages/foo.yaml', '')

        doc = pod.get_doc('/content/pages/foo@en_us.yaml')
        self.assertEqual([
            '/content/pages/foo@en_us.yaml',
            '/content/pages/foo@en.yaml',
            '/content/pages/foo.yaml',
        ], doc.locale_paths)

        doc = pod.get_doc('/content/pages/foo@en.yaml')
        self.assertEqual([
            '/content/pages/foo@en.yaml',
            '/content/pages/foo.yaml',
        ], doc.locale_paths)

        doc = pod.get_doc('/content/pages/foo.yaml')
        self.assertEqual([
            '/content/pages/foo.yaml',
        ], doc.locale_paths)

    def test_dependency_nesting_jinja(self):
        # Verify that dependencies work for nested documents.

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
            '$localization': {
                'path': '/{locale}/{base}/'
            },
        })
        pod.write_file('/content/pages/page.yaml', 'partial: !g.doc /content/partials/partial.yaml')
        pod.write_yaml('/content/partials/_blueprint.yaml', {})
        pod.write_yaml('/content/partials/partial.yaml', {})
        pod.write_yaml('/content/partials/partial@de.yaml', {})
        pod.write_file(
            '/views/base.html',
            '{}{} {}'.format(
                '{{doc.locale}}',
                '{% for partial in g.docs(\'partials\') %} {{partial.locale}}{% endfor %}',
                '{{g.doc(\'/content/partials/partial.yaml\').locale}}',
            ),
        )

        controller, params = pod.match('/page/')
        content = controller.render(params)
        self.assertEqual('en en en', content)

        dependents = pod.podcache.dependency_graph.get_dependents(
            '/content/partials/partial.yaml')
        self.assertEqual(set([
            '/content/partials/partial.yaml',
            '/content/pages/page.yaml',
        ]), dependents)

        controller, params = pod.match('/de/page/')
        content = controller.render(params)
        self.assertEqual('de de de', content)

        dependents = pod.podcache.dependency_graph.get_dependents(
            '/content/partials/partial@de.yaml')
        self.assertEqual(set([
            '/content/partials/partial@de.yaml',
            '/content/pages/page.yaml',
        ]), dependents)

    def test_dependency_nesting_yaml(self):
        # Verify that dependencies work for nested documents.

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
            '$localization': {
                'path': '/{locale}/{base}/'
            },
        })
        pod.write_file('/content/pages/page.yaml', 'partial: !g.doc /content/partials/partial.yaml')
        pod.write_yaml('/content/partials/_blueprint.yaml', {})
        pod.write_yaml('/content/partials/partial.yaml', {})
        pod.write_yaml('/content/partials/partial@de.yaml', {})
        pod.write_file('/views/base.html', '{{doc.locale}} {{doc.partial.locale}}')

        controller, params = pod.match('/page/')
        content = controller.render(params)
        self.assertEqual('en en', content)

        dependents = pod.podcache.dependency_graph.get_dependents(
            '/content/partials/partial.yaml')
        self.assertEqual(set([
            '/content/partials/partial.yaml',
            '/content/pages/page.yaml',
        ]), dependents)

        controller, params = pod.match('/de/page/')
        content = controller.render(params)
        self.assertEqual('de de', content)

        dependents = pod.podcache.dependency_graph.get_dependents(
            '/content/partials/partial@de.yaml')
        self.assertEqual(set([
            '/content/partials/partial@de.yaml',
            '/content/pages/page.yaml',
        ]), dependents)

    def test_yaml_dump(self):
        """Test if the yaml representer is working correctly."""
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/page.yaml', {})
        doc = pod.get_doc('/content/pages/page.yaml')
        input_obj = {
            'doc': doc
        }
        expected = textwrap.dedent(
            """\
            doc: !g.doc '/content/pages/page.yaml'
            """)

        self.assertEqual(expected, utils.dump_yaml(input_obj))


if __name__ == '__main__':
    unittest.main()
