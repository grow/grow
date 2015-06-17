from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class DocumentsTestCase(unittest.TestCase):

  def setUp(self):
    dir_path = testing.create_test_pod_dir()
    self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

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
        '$title',
        '$view',
        '$path',
        '$order',
        '$localization',
        'foo',
        'translation_with_priority',
        'tagged_fields',
    ]
    self.assertItemsEqual(keys, doc.fields.keys())
    self.assertIsNone(doc.html)

    default_doc = self.pod.get_doc('/content/pages/about.yaml')
    self.assertEqual('bar', default_doc.foo)

    de_doc = self.pod.get_doc('/content/pages/about.yaml', locale='de')
    self.assertEqual('baz', de_doc.foo)
    self.assertEqual('qux', de_doc.qaz)

    doc = self.pod.get_doc('/content/pages/home.yaml', locale='de')
    self.assertEqual('Higher Priority', doc.translation_with_priority)

    doc = self.pod.get_doc('/content/pages/home.yaml', locale='ja')
    self.assertEqual('Lower Priority', doc.translation_with_priority)


if __name__ == '__main__':
  unittest.main()
