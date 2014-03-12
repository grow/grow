from grow.pods import locales
from grow.pods import pods
from grow.pods import storage
from grow.pods.controllers import page
import unittest


class PageTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_ll(self):
    routes = self.pod.get_routes()
    print routes.to_message()
    controller = routes.match('/')
    self.assertEqual(page.PageController.Defaults.LL, controller.ll)
    controller = routes.match('/de/about/')
    de_locale = locales.Locale.parse('de')
    self.assertEqual(de_locale, controller.locale)

  def test_mimetype(self):
    routes = self.pod.get_routes()
    controller = routes.match('/')
    self.assertEqual('text/html', controller.mimetype)
    controller = routes.match('/de/about/')
    self.assertEqual('text/html', controller.mimetype)

  def test_render(self):
    routes = self.pod.get_routes()
    controller = routes.match('/')
    controller.render()
    controller = routes.match('/de/about/')
    controller.render()

  def test_list_concrete_paths(self):
    routes = self.pod.get_routes()
    controller = routes.match('/')
    self.assertEqual(['/'], controller.list_concrete_paths())


if __name__ == '__main__':
  unittest.main()

