from . import builtins
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class BuiltinsTestCase(unittest.TestCase):

  def setUp(self):
    self.dir_path = testing.create_test_pod_dir()
    self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

  def test_slug_filter(self):
    words = 'Foo Bar Baz'
    self.assertEqual('foo-bar-baz', builtins.slug_filter(words))

  def test_json(self):
    controller = self.pod.match('/yaml_test/')
    html = controller.render()
    self.assertIn('key - value', html)
    self.assertIn('key2 - value2', html)

  def test_collections(self):
    collections = builtins.collections(_pod=self.pod)
    self.assertEqual(4, len(collections))
    paths = ['pages', 'posts']
    collections = builtins.collections(paths, _pod=self.pod)
    for collection in collections:
      self.assertIn(collection.collection_path, paths)
    self.assertEqual(len(paths), len(collections))


if __name__ == '__main__':
  unittest.main()
