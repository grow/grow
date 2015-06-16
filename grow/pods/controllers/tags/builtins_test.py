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


if __name__ == '__main__':
  unittest.main()
