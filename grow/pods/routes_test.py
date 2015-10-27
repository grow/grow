from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest
import webob.exc


class RoutesTest(unittest.TestCase):

  def setUp(self):
    self.maxDiff = None
    self.dir_path = testing.create_test_pod_dir()
    self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

  def test_match(self):
    controller = self.pod.match('/')
    controller.render()
    controller = self.pod.match('/fr/about/')
    controller.render()
    controller = self.pod.match('/de_alias/about/')
    controller.render()
    self.assertRaises(webob.exc.HTTPNotFound, self.pod.match, '/dummy/')
    controller = self.pod.match('/app/static/file with spaces.txt')
    controller.render()

  def test_list_concrete_paths(self):
    expected = [
        '/',
        '/about/',
        '/app/static/file with spaces.txt',
        '/app/static/somepath/de_alias/test.txt',
        '/app/static/test.txt',
        '/de_alias/about/',
        '/de_alias/contact-us/',
        '/de_alias/home/',
        '/de_alias/html/',
        '/de_alias/intro/',
        '/de_alias/yaml_test/',
        '/fi_ALL/about/',
        '/fi_ALL/home/',
        '/fi_ALL/html/',
        '/fi_ALL/intro/',
        '/fi_ALL/yaml_test/',
        '/fil_ALL/about/',
        '/fil_ALL/home/',
        '/fil_ALL/html/',
        '/fil_ALL/intro/',
        '/fil_ALL/yaml_test/',
        '/fr/about/',
        '/fr/contact-us/',
        '/fr/home/',
        '/fr/html/',
        '/fr/intro/',
        '/fr/yaml_test/',
        '/html/',
        '/intl/de_alias/localized/',
        '/intl/de_alias/multiple-locales/',
        '/intl/en/localized/',
        '/intl/en_gb/localized/',
        '/intl/en_pk/localized-view/',
        '/intl/fr/localized/',
        '/intl/fr/multiple-locales/',
        '/intl/hi_in/localized/',
        '/intl/it/multiple-locales/',
        '/intl/ja/localized/',
        '/intl/tr_tr/localized-view/',
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
        '/root/base/',
        '/root/static/file.txt',
        '/yaml_test/',
    ]
    result = self.pod.routes.list_concrete_paths()
    self.assertItemsEqual(expected, result)


if __name__ == '__main__':
  unittest.main()
