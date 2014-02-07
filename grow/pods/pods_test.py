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
    self.pod.dump()

  def test_to_message(self):
    self.pod.to_message()


if __name__ == '__main__':
  unittest.main()
