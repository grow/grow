from grow.pods import pods
from grow.pods import storage
import unittest
import webob.exc


class RoutesTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_match(self):
    self.pod.match('/')
    self.pod.match('/de/about/')
    self.assertRaises(webob.exc.HTTPNotFound, self.pod.match, '/dummy/')

  def test_list_concrete_paths(self):
    expected = [
        '/',
        '/about/',
        '/contact-us/',
        '/de/about/',
        '/de/contact-us/',
        '/de/home/',
        '/de/html/',
        '/de/intro/',
        '/de/yaml_test/',
        '/fr/about/',
        '/fr/contact-us/',
        '/fr/home/',
        '/fr/html/',
        '/fr/intro/',
        '/fr/yaml_test/',
        '/html/',
        '/intro/',
        '/it/about/',
        '/it/contact-us/',
        '/it/home/',
        '/it/html/',
        '/it/intro/',
        '/it/yaml_test/',
        '/post/newer/',
        '/post/newest/',
        '/post/older/',
        '/post/oldest/',
        '/public/file.txt',
        '/public/main.css',
        '/public/main.min.js',
        '/yaml_test/',
    ]
    result = self.pod.routes.list_concrete_paths()
    self.assertItemsEqual(expected, result)


if __name__ == '__main__':
  unittest.main()
