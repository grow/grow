from grow.pods import pods
from grow.pods.blueprints import blueprints
from grow.pods.blueprints import messages
from grow.pods import storage
import unittest


class BlueprintsTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_get(self):
    blueprint = blueprints.Blueprint.get('pages', pod=self.pod)
    self.assertEqual('pages', blueprint.nickname)

  def test_list(self):
    blueprints.Blueprint.list(self.pod)

  def test_list_documents(self):
    blueprint = blueprints.Blueprint.get('pages', pod=self.pod)
    documents = blueprint.list_documents()
    expected = ['home', 'about', 'contact',]
    self.assertListEqual(expected, [doc.slug for doc in documents])

    blueprint = blueprints.Blueprint.get('posts', pod=self.pod)
    documents = blueprint.list_documents(order_by='published', reverse=True)
    expected = ['newest', 'newer', 'older', 'oldest']
    self.assertListEqual(expected, [doc.slug for doc in documents])

  def test_search(self):
    blueprint = blueprints.Blueprint.get('pages', pod=self.pod)
    blueprint.search()

  def test_list_servable_documents(self):
    blueprint = blueprints.Blueprint.get('pages', pod=self.pod)
    blueprint.list_servable_documents()

  def test_format(self):
    blueprint = blueprints.Blueprint.get('posts', pod=self.pod)
    doc = blueprint.get_document('newer.yaml')
    self.assertEqual(doc.format, messages.Format.HTML)

    doc = blueprint.get_document('newest.md')
    self.assertEqual(doc.format, messages.Format.MARKDOWN)
    self.assertEqual('<h1>Markdown</h1>', doc.body)


if __name__ == '__main__':
  unittest.main()
