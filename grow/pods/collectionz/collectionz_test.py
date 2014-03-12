from grow.pods import pods
from grow.pods.collectionz import collectionz
from grow.pods.collectionz import messages
from grow.pods import locales
from grow.pods import storage
import unittest


class CollectionsTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_get(self):
    self.pod.get_collection('/content/pages/')

  def test_list(self):
    collectionz.Collection.list(self.pod)

  def test_list_documents(self):
    # List documents where locale = fr.
    collection = self.pod.get_collection('pages')
    documents = collection.list_documents(locale='fr')
    for doc in documents:
      self.assertEqual('fr', doc.locale)

    # List all documents.
    documents = collection.list_documents()

    collection = self.pod.get_collection('posts')
    documents = collection.list_documents(order_by='$published', reverse=True)
    expected = ['newest', 'newer', 'older', 'oldest']
    self.assertListEqual(expected, [doc.base for doc in documents])

  def test_list_locales(self):
    collection = self.pod.get_collection('pages')
    found_locales = collection.list_locales()
    expected = locales.Locale.parse_codes(['de', 'en', 'fr', 'it'])
    self.assertListEqual(expected, found_locales)

  def test_list_servable_documents(self):
    collection = self.pod.get_collection('pages')
    collection.list_servable_documents()

  def test_format(self):
    collection = self.pod.get_collection('posts')
    doc = collection.get_doc('/content/posts/newer.md')
    self.assertEqual(doc.format, messages.Format.MARKDOWN)

    doc = collection.get_doc('/content/posts/newest.md')
    self.assertEqual(doc.format, messages.Format.MARKDOWN)
    self.assertEqual('# Markdown', doc.body)
    self.assertEqual('<h1 id="markdown">Markdown</h1>', doc.html)


if __name__ == '__main__':
  unittest.main()
