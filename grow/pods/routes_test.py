from grow.pods import pods
from grow.pods import storage
from grow.pods import routes as routes_lib
import unittest


class RoutesTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_match(self):
    routes = self.pod.get_routes()
    routes.match('/')
    routes.match('/de/about/')
    self.assertRaises(routes_lib.Errors.NotFound, routes.match, '/dummy/')

  def test_list_concrete_paths(self):
    expected = [
        '/',
        '/about/',
        '/contact-us/',
        '/de/about/',
        '/de/contact/',
        '/de/home/',
        '/fr/about/',
        '/fr/contact/',
        '/fr/home/',
        '/it/about/',
        '/it/contact/',
        '/it/home/',
        '/post/newer/',
        '/post/newest/',
        '/post/older/',
        '/post/oldest/',
        '/public/file.txt',
        '/public/main.css',
        '/public/main.min.js',
    ]
    result = self.pod.routes.list_concrete_paths()
    self.assertItemsEqual(expected, result)


if __name__ == '__main__':
  unittest.main()
