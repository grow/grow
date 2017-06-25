from . import tags
from grow.pods import locales
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class BuiltinsTestCase(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_shuffle_filter(self):
        words = ['foo', 'bar', 'baz']
        self.assertIn('foo', tags.shuffle_filter(None, words))

    def test_slug_filter(self):
        words = 'Foo Bar Baz'
        self.assertEqual('foo-bar-baz', tags.slug_filter(words))

        words = 'Foo\'s b@z b**'
        self.assertEqual('foo-s-b-z-b', tags.slug_filter(words))

    def test_locale(self):
        identifier = 'de'
        expected = locales.Locale.parse(identifier)
        self.assertEqual(expected, tags.locale(identifier))

    def test_locales(self):
        identifiers = ['de']
        expected = locales.Locale.parse_codes(identifiers)
        self.assertEqual(expected, tags.locales(identifiers))

    def test_json(self):
        controller, params = self.pod.match('/yaml_test/')
        html = controller.render(params)
        self.assertIn('key - value', html)
        self.assertIn('key2 - value2', html)

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


if __name__ == '__main__':
    unittest.main()
