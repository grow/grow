from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class StaticTest(unittest.TestCase):

  def setUp(self):
    self.dir_path = testing.create_test_pod_dir()
    self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

  def test_static(self):
    static = self.pod.get_static('/static/test.txt')
    self.assertEqual('/app/static/test.txt', static.url.path)
    static = self.pod.get_static('/static/test.txt', locale='de')
    self.assertEqual('/app/static/somepath/de/test.txt', static.url.path)


if __name__ == '__main__':
  unittest.main()
