from grow.pods import pods
from grow.pods import storage
import os
import unittest

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata', 'pod')


class PodTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_list_dir(self):
    os.listdir(os.path.join(TESTDATA_DIR, 'content'))
    self.pod.list_dir('/content')

  def test_read_file(self):
    content = self.pod.read_file('/README.md')
    path = os.path.join(TESTDATA_DIR, 'README.md')
    expected_content = open(path).read()
    self.assertEqual(expected_content, content)

  def test_write_file(self):
    path = '/dummy.yaml'
    self.pod.write_file(path, 'foo')
    content = self.pod.read_file(path)
    self.assertEqual('foo', content)

    self.pod.write_file(path, 'bar')
    content = self.pod.read_file(path)
    self.assertEqual('bar', content)

  def test_list_collections(self):
    self.pod.list_collections()

  def test_export(self):
    self.pod.export()

  def test_dump(self):
    paths = [
        '/about/index.html',
        '/contact-us/index.html',
        '/de/about/index.html',
        '/de/contact-us/index.html',
        '/de/home/index.html',
        '/de/html/index.html',
        '/de/intro/index.html',
        '/fr/about/index.html',
        '/fr/contact-us/index.html',
        '/fr/home/index.html',
        '/fr/html/index.html',
        '/fr/intro/index.html',
        '/html/index.html',
        '/index.html',
        '/intro/index.html',
        '/it/about/index.html',
        '/it/contact-us/index.html',
        '/it/home/index.html',
        '/it/html/index.html',
        '/it/intro/index.html',
        '/post/newer/index.html',
        '/post/newest/index.html',
        '/post/older/index.html',
        '/post/oldest/index.html',
        '/public/file.txt',
        '/public/main.css',
        '/public/main.min.js',
    ]
    result = self.pod.dump()
    self.assertItemsEqual(paths, result)

  def test_to_message(self):
    self.pod.to_message()

  def test_list_deployments(self):
    self.pod.list_deployments()


if __name__ == '__main__':
  unittest.main()
