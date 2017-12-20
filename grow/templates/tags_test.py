"""Tests for the template tags and filters."""

import unittest
from grow.translations import locales
from grow.pods import pods
from grow import storage
from grow.templates import tags
from grow.testing import testing


class BuiltinsTestCase(unittest.TestCase):

    def _render_path(self, pod, path):
        routes = pod.router.routes
        matched = routes.match(path)
        controller = pod.router.get_render_controller(
            matched.path, matched.value, params=matched.params)
        jinja_env = pod.render_pool.get_jinja_env(
            controller.doc.locale)
        rendered_doc = controller.render(jinja_env=jinja_env)
        return rendered_doc.read()

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_locale_tag(self):
        identifier = 'de'
        expected = locales.Locale.parse(identifier)
        self.assertEqual(expected, tags.locale_tag(identifier))

    def test_locales_tag(self):
        identifiers = ['de']
        expected = locales.Locale.parse_codes(identifiers)
        self.assertEqual(expected, tags.locales_tag(identifiers))

    def test_collections(self):
        collections = tags.collections(_pod=self.pod)
        self.assertEqual(4, len(collections))
        paths = ['pages', 'posts']
        collections = tags.collections(paths, _pod=self.pod)
        for collection in collections:
            self.assertIn(collection.collection_path, paths)
        self.assertEqual(len(paths), len(collections))

    def test_categories(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        fields = {
            'path': '/{base}/',
            'view': '/views/base.html',
            'categories': [
                'Category1',
                'Category2',
                'Category3',
                'Category4',
                'Category5',
            ],
        }

        # Verify default behavior.
        pod.write_yaml('/content/collection/_blueprint.yaml', fields)
        pod.write_yaml('/content/collection/doc1.yaml', {
            '$category': 'Category1',
            '$order': 1,
        })
        pod.write_yaml('/content/collection/doc2.yaml', {
            '$category': 'Category1',
            '$order': 2,
        })
        pod.write_yaml('/content/collection/doc3.yaml', {
            '$category': 'Category2',
        })
        result = tags.categories(collection='collection', _pod=pod)

        doc1 = pod.get_doc('/content/collection/doc1.yaml')
        doc2 = pod.get_doc('/content/collection/doc2.yaml')
        doc3 = pod.get_doc('/content/collection/doc3.yaml')
        expected = [
            ('Category1', [doc1, doc2]),
            ('Category2', [doc3]),
        ]
        self.assertEqual(expected, result)

        # Verify localized behavior.
        fields.update({
            'localization': {
                'locales': [
                    'en',
                ],
            }
        })
        pod.write_yaml('/content/collection/_blueprint.yaml', fields)
        pod.write_yaml('/content/collection/doc1@de.yaml', {
            '$category': 'Category3',
        })
        pod.write_yaml('/content/collection/doc2@de.yaml', {
            '$category': 'Category3',
        })
        pod.write_yaml('/content/collection/doc4@de.yaml', {
            '$category': 'Category6',
        })
        result = tags.categories(collection='collection', locale='de', _pod=pod)
        result = [item[0] for item in result]
        expected = ['Category3', 'Category6',]
        self.assertEqual(expected, result)

    def test_default_locale_versus_no_locale(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en_US',
                'locales': [
                    'en_US',
                    'ja_JP',
                ],
            },
        })
        fields = {
            'path': '/{locale}/{base}/',
            'view': '/views/base.html',
            'localization': {
                'path': '/{locale}/{base}/',
            },
        }
        pod.write_yaml('/content/pages/_blueprint.yaml', fields)
        pod.write_yaml('/content/pages/doc1.yaml', {
            '$localization': {
                'default_locale': 'ja_JP',
                'locales': [
                    'ja_JP',
                ],
            }
        })
        pod.write_yaml('/content/pages/doc2.yaml', {
            '$localization': {
                'locales': [
                    'en_US',
                ],
            }
        })
        pod.write_yaml('/content/pages/doc3.yaml', {})

        # Verify `docs` locale kwarg behavior, should default to calling
        # document's locale. Verify a calling en_US doc only gets en_US docs.
        doc = pod.get_doc('/content/pages/doc3.yaml')
        tags_in_context = tags.create_builtin_tags(pod, doc)
        docs = tags_in_context['docs']('pages')
        self.assertItemsEqual([
            '/content/pages/doc2.yaml',
            '/content/pages/doc3.yaml',
        ], [doc.pod_path for doc in docs])

        # Verify a calling ja_JP doc only gets ja_JP docs.
        doc = pod.get_doc('/content/pages/doc1.yaml')
        tags_in_context = tags.create_builtin_tags(pod, doc)
        docs = tags_in_context['docs']('pages')
        self.assertItemsEqual([
            '/content/pages/doc1.yaml',
            '/content/pages/doc3.yaml',
        ], [doc.pod_path for doc in docs])

        # Verify an explicit `locale=None` returns all docs regardless of the
        # calling document's locale.
        doc = pod.get_doc('/content/pages/doc1.yaml')
        tags_in_context = tags.create_builtin_tags(pod, doc)
        docs = tags_in_context['docs']('pages', locale=None)
        self.assertItemsEqual([
            '/content/pages/doc1.yaml',
            '/content/pages/doc2.yaml',
            '/content/pages/doc3.yaml',
        ], [doc.pod_path for doc in docs])
        doc = pod.get_doc('/content/pages/doc2.yaml')
        tags_in_context = tags.create_builtin_tags(pod, doc)
        docs = tags_in_context['docs']('pages', locale=None)
        self.assertItemsEqual([
            '/content/pages/doc1.yaml',
            '/content/pages/doc2.yaml',
            '/content/pages/doc3.yaml',
        ], [doc.pod_path for doc in docs])

    def test_gettext_format(self):
        """Verify that the gettext formatting works."""
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en',
                'locales': [
                    'en',
                    'es',
                ],
            },
        })
        pod.write_file('/views/format.html', '{{_(doc.foo, bar="1", foo="2")}}')
        fields = {
            'path': '/{locale}/{base}/',
            'localization': {
                'path': '/{locale}/{base}/',
            },
        }
        pod.write_yaml('/content/testing/_blueprint.yaml', fields)
        pod.write_yaml('/content/testing/format.yaml', {
            '$view': '/views/format.html',
            'foo': 'bar {bar} foo {foo}',
            'foo@es': 'foo {foo} bar {bar}',
        })

        pod.router.add_doc(
            pod.get_doc('/content/testing/format.yaml'))
        pod.router.add_doc(
            pod.get_doc('/content/testing/format.yaml', locale='es'))

        self.assertIn('bar 1 foo 2', self._render_path(pod, '/en/format/'))
        self.assertIn('foo 2 bar 1', self._render_path(pod, '/es/format/'))

    def test_gettext_format_entities(self):
        """Verify that the gettext formatting works with entities."""
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_file(
            '/views/format-old.html',
            '{{_(\'Hello %(name)s\', name=\'<strong class="awesome">Alice</strong>\')}}')
        pod.write_file(
            '/views/format-new.html',
            '{{_(\'Hello {name}\', name=\'<strong class="awesome">Alice</strong>\')}}')
        pod.write_yaml('/content/testing/_blueprint.yaml', {
            'path': '/{base}/',
        })
        pod.write_yaml('/content/testing/format-old.yaml', {
            '$view': '/views/format-old.html',
        })
        pod.write_yaml('/content/testing/format-new.yaml', {
            '$view': '/views/format-new.html',
        })

        pod.router.add_doc(
            pod.get_doc('/content/testing/format-old.yaml'))
        pod.router.add_doc(
            pod.get_doc('/content/testing/format-new.yaml'))

        self.assertIn(
            'Hello <strong class="awesome">Alice</strong>',
            self._render_path(pod, '/format-old/'))
        self.assertIn(
            'Hello <strong class="awesome">Alice</strong>',
            self._render_path(pod, '/format-new/'))


if __name__ == '__main__':
    unittest.main()
