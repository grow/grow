from grow.pods import pods
from grow.pods import storage
from grow.pods import routes
import unittest


class RoutesTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_match(self):
    self.pod.routes.match('/', domain='example.com')
    self.assertRaises(routes.Errors.NotFound, self.pod.routes.match, '/dummy')

  def test_list_concrete_paths(self):
    expected = [
        '/',
        '/<grow:ll>/about',
        '/contact',
        '/public/file.txt',
        '/public/main.min.js',
    ]
    result = self.pod.routes.list_concrete_paths()
    self.assertItemsEqual(expected, result)


if __name__ == '__main__':
  unittest.main()
