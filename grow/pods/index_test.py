from grow.pods import pods
from grow.pods import index
from grow.pods import storage
import unittest


class IndexTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_diff(self):
    my_index = index.Index()
    my_index.update({
      '/file.txt': 'test',
      '/file2.txt': 'test',
      '/foo/file.txt': 'test',
      '/foo/file.txt': 'test',
    })
    their_index = index.Index()
    their_index.update({
      '/file2.txt': 'change',
      '/foo/file.txt': 'test',
      '/foo/file.txt': 'test',
      '/bar/new.txt': 'test',
    })
    expected = index.Index.Diff(
        adds=['/file.txt'],
        edits=['/file2.txt'],
        deletes=['/bar/new.txt'],
        nochanges=['/foo/file.txt'],
    )
    self.assertEqual(expected, my_index.diff(their_index))


if __name__ == '__main__':
  unittest.main()

