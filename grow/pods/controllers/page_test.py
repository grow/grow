from grow.pods import locales
from grow.pods import pods
from grow.pods import storage
from grow.pods.controllers import page
import unittest


class PageTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_ll(self):
    controller = self.pod.match('/')
    self.assertEqual(page.PageController.Defaults.LL, controller.ll)
    controller = self.pod.match('/de/about/')
    de_locale = locales.Locale.parse('de')
    self.assertEqual(de_locale, controller.locale)

  def test_mimetype(self):
    controller = self.pod.match('/')
    self.assertEqual('text/html', controller.mimetype)
    controller = self.pod.match('/de/about/')
    self.assertEqual('text/html', controller.mimetype)

  def test_render(self):
    controller = self.pod.match('/')
    controller.render()
    controller = self.pod.match('/de/about/')
    controller.render()

  def test_list_concrete_paths(self):
    controller = self.pod.match('/')
    self.assertEqual(['/'], controller.list_concrete_paths())


if __name__ == '__main__':
  unittest.main()

