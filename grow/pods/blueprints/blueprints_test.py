from grow.pods import pods
from grow.pods.blueprints import blueprints
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
    expected = [
        '/content/pages/about.yaml',
        '/content/pages/home.yaml',
        '/content/pages/contact.yaml',
    ]
    self.assertItemsEqual(expected, [doc.pod_path for doc in documents])

  def test_search(self):
    blueprint = blueprints.Blueprint.get('pages', pod=self.pod)
    blueprint.search()

  def test_list_servable_documents(self):
    blueprint = blueprints.Blueprint.get('pages', pod=self.pod)
    blueprint.list_servable_documents()


if __name__ == '__main__':
  unittest.main()

