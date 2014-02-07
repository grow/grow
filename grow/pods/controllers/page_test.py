from grow.pods import pods
from grow.pods import storage
from grow.pods.controllers import page
import unittest


class PageTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_ll(self):
    routes = self.pod.get_routes()
    controller = routes.match('/')
    self.assertEqual(page.PageController.Defaults.LL, controller.ll)
    controller = routes.match('/de/about/')
    self.assertEqual('de', controller.locale)

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

