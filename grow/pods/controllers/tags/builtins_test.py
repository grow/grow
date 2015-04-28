from . import builtins
from grow.pods import pods
from grow.pods import storage
import unittest


class BuiltinsTestCase(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_slug_filter(self):
    words = 'Foo Bar Baz'
    self.assertEqual('foo-bar-baz', builtins.slug_filter(words))


if __name__ == '__main__':
  unittest.main()
