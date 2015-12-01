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
    self.assertEqual('/app/root/static/somepath/de_alias/test.txt',
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

    fingerprint = '961109f2e6cc139a8f6df6e3a307c247'
    static = self.pod.get_static(
        '/static-fingerprint/fingerprinted.txt')
    self.assertEqual(
        '/root/static-fingerprint/{}/fingerprinted.txt'.format(fingerprint),
        static.url.path)
    static = self.pod.get_static(
        '/static-fingerprint/fingerprinted.txt', locale='de')
    fingerprint = 'bc20b3c9007842b8e1f3c640b07f4e74'
    self.assertEqual(
        '/root/static-fingerprint/{}/de_alias/fingerprinted.txt'.format(fingerprint),
        static.url.path)


if __name__ == '__main__':
  unittest.main()
