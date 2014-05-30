from . import indexes
from . import messages
from grow.pods import pods
from grow.pods import storage
import unittest


class IndexTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_diff(self):
    my_index = indexes.Index()
    my_index.update({
      '/file.txt': 'test',
      '/file2.txt': 'test',
      '/foo/file.txt': 'test',
      '/foo/file.txt': 'test',
    })
    their_index = indexes.Index()
    their_index.update({
      '/file2.txt': 'change',
      '/foo/file.txt': 'test',
      '/foo/file.txt': 'test',
      '/bar/new.txt': 'test',
    })
    expected = messages.DiffMessage(
        adds=[messages.FileMessage(path='/file.txt')],
        edits=[messages.FileMessage(path='/file2.txt')],
        deletes=[messages.FileMessage(path='/bar/new.txt')],
        nochanges=[messages.FileMessage(path='/foo/file.txt')],
    )
    self.assertEqual(expected, my_index.create_diff(their_index))


if __name__ == '__main__':
  unittest.main()

