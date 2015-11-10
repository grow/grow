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
    static_de = self.pod.get_static('/static/test.txt', locale='de')
    self.assertEqual('/app/static/somepath/de_alias/test.txt',
                     static_de.url.path)
    static_same = self.pod.get_static('/static/test.txt')
    self.assertEqual(static, static_same)
    self.assertNotEqual(static, static_de)
    self.assertEqual('test', static.base)
    self.assertIsNotNone(static.modified)
    self.assertTrue(static.exists)
    self.assertEqual('.txt', static.ext)
    static = self.pod.get_static('/static/file with spaces.txt')
    self.assertEqual('/app/static/file with spaces.txt', static.url.path)


if __name__ == '__main__':
  unittest.main()
