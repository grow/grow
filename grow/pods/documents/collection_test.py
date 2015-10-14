from grow.pods import locales
from grow.pods import pods
from grow.pods import storage
from grow.pods.documents import collection
from grow.testing import testing
import unittest


class CollectionsTestCase(unittest.TestCase):

  def setUp(self):
    dir_path = testing.create_test_pod_dir()
    self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

  def test_get(self):
    self.pod.get_collection('/content/pages/')

  def test_list(self):
    collection.Collection.list(self.pod)

  def test_list_docs(self):
    # List documents where locale = fr.
    collection = self.pod.get_collection('pages')
    documents = collection.list_docs(locale='fr')
    for doc in documents:
      self.assertEqual('fr', doc.locale)
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
    found_locales = collection.list_locales()
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


if __name__ == '__main__':
  unittest.main()
