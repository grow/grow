from . import collection
from . import locales
from . import pods
from . import storage
from grow.testing import testing
import unittest


class CollectionsTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_get(self):
        col = self.pod.get_collection('/content/pages/')
        self.assertEqual('pages', col.collection_path)
        col2 = self.pod.get_collection('pages')
        docs = col2.list_docs()
        self.assertEqual(col, col2)
        self.assertEqual(col, docs[0].collection)

    def test_list(self):
        collection.Collection.list(self.pod)

    def test_list_docs(self):
        # List documents where locale = fr.
        collection = self.pod.get_collection('pages')
        documents = collection.list_docs(locale='fr')
        for doc in documents:
            self.assertEqual('fr', doc.locale)

        # Verify list behavior with multi-file localized documents.
        expected_docs = [
            self.pod.get_doc(pod_path, locale='fr')
            for pod_path in [
                '/content/pages/yaml_test.html',
                '/content/pages/home.yaml',
                '/content/pages/intro@fr.md',
                '/content/pages/about.yaml',
                '/content/pages/contact.yaml',
            ]
        ]
        for i, doc in enumerate(expected_docs):
            self.assertEqual(doc, documents[i])

        # List unhidden documents.
        documents = collection.list_docs()
        for doc in documents:
            self.assertFalse(doc.hidden)

        # List all documents.
        documents = collection.list_docs(include_hidden=True)
        collection = self.pod.get_collection('posts')
        documents = collection.list_docs(order_by='$published', reverse=True)
        expected = ['newest', 'newer', 'older', 'oldest']
        self.assertListEqual(expected, [doc.base for doc in documents])

    def test_list_locales(self):
        collection = self.pod.get_collection('pages')
        found_locales = collection.locales
        expected = locales.Locale.parse_codes([
            'de',
            'en',
            'fi',
            'fil',
            'fr',
            'it',
        ])
        self.assertListEqual(expected, found_locales)

    def test_list_servable_documents(self):
        collection = self.pod.get_collection('pages')
        collection.list_servable_documents()

    def test_format(self):
        collection = self.pod.get_collection('posts')
        doc = collection.get_doc('/content/posts/newest.md')
        self.assertEqual('# Markdown', doc.body)
        self.assertEqual('<h1 id="markdown">Markdown</h1>', doc.html)

    def test_empty_front_matter(self):
        collection = self.pod.get_collection('empty-front-matter')
        docs = collection.list_docs()
        path = '/content/empty-front-matter/empty-front-matter.html'
        expected_doc = self.pod.get_doc(path)
        self.assertEqual(expected_doc, docs[0])

    def test_collections(self):
        collection = self.pod.create_collection('new', {})
        self.assertEqual([],
              [col for col in collection.collections()])
        sub_collection = self.pod.create_collection('new/sub', {})
        self.assertEqual([sub_collection],
              [col for col in collection.collections()])
        sub_sub_collection = self.pod.create_collection('new/sub/sub', {})
        self.assertEqual([sub_collection],
              [col for col in collection.collections()])
        self.assertEqual([sub_sub_collection],
              [col for col in sub_collection.collections()])

    def test_nested_collections(self):
        # While it was undefined behavior before, projects relied on the
        # ability to place documents in subfolders inside collections without
        # explicit _blueprint.yaml files inside those folders. Verify that
        # paths are still generated for those documents.
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_file('/views/base.html', '')
        fields = {
            'path': '/{base}/',
            'view': '/views/base.html',
        }
        pod.write_yaml('/content/collection/_blueprint.yaml', fields)
        pod.write_yaml('/content/collection/root.yaml', {})
        pod.write_yaml('/content/collection/folder/folder.yaml', {})
        pod.write_yaml('/content/collection/folder/subfolder/subfolder.yaml', {})
        pod.write_yaml('/content/collection/folder2/subfolder2/subfolder2.yaml', {})
        expected = [
            '/root/',
            '/folder/',
            '/subfolder/',
            '/subfolder2/',
        ]
        self.assertItemsEqual(expected, pod.routes.list_concrete_paths())


if __name__ == '__main__':
    unittest.main()
