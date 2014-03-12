from grow.pods import pods
from grow.pods import storage
import unittest
import webob.exc


class RoutesTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_match(self):
    routes = self.pod.get_routes()
    routes.match('/')
    routes.match('/de/about/')
    self.assertRaises(webob.exc.HTTPNotFound, routes.match, '/dummy/')

  def test_list_concrete_paths(self):
    expected = [
        '/',
        '/about/',
        '/contact-us/',
        '/intro/',
        '/de/about/',
        '/de/contact/',
        '/de/home/',
        '/de/intro/',
        '/fr/about/',
        '/fr/contact/',
        '/fr/home/',
        '/fr/intro/',
        '/it/about/',
        '/it/contact/',
        '/it/home/',
        '/it/intro/',
        '/post/newer/',
        '/post/newest/',
        '/post/older/',
        '/post/oldest/',
        '/public/file.txt',
        '/public/main.css',
        '/public/main.min.js',
    ]
    result = self.pod.routes.list_concrete_paths()
    print result
    self.assertItemsEqual(expected, result)


if __name__ == '__main__':
  unittest.main()
