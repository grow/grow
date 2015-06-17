from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import os
import unittest


class PodTest(unittest.TestCase):

  def setUp(self):
    self.dir_path = testing.create_test_pod_dir()
    self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

  def test_list_dir(self):
    os.listdir(os.path.join(self.dir_path, 'content'))
    self.pod.list_dir('/content')

  def test_read_file(self):
    content = self.pod.read_file('/README.md')
    path = os.path.join(self.dir_path, 'README.md')
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
        '/de/yaml_test/index.html',
        '/fr/about/index.html',
        '/fr/contact-us/index.html',
        '/fr/home/index.html',
        '/fr/html/index.html',
        '/fr/intro/index.html',
        '/fr/yaml_test/index.html',
        '/html/index.html',
        '/index.html',
        '/intro/index.html',
        '/it/about/index.html',
        '/it/contact-us/index.html',
        '/it/home/index.html',
        '/it/html/index.html',
        '/it/intro/index.html',
        '/it/yaml_test/index.html',
        '/post/newer/index.html',
        '/post/newest/index.html',
        '/post/older/index.html',
        '/post/oldest/index.html',
        '/public/file.txt',
        '/public/main.css',
        '/public/main.min.js',
        '/yaml_test/index.html',
    ]
    result = self.pod.dump()
    self.assertItemsEqual(paths, result)

  def test_to_message(self):
    self.pod.to_message()

  def test_list_deployments(self):
    self.pod.list_deployments()


if __name__ == '__main__':
  unittest.main()
