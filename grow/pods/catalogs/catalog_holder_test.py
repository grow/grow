from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class CatalogsTest(unittest.TestCase):

  def setUp(self):
    dir_path = testing.create_test_pod_dir()
    self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
    self.pod.catalogs.compile()

  def test_list_locales(self):
    self.assertItemsEqual(
        ['de', 'fr', 'en', 'it', 'ja'],
        self.pod.catalogs.list_locales())

  def test_extract(self):
    template_catalog = self.pod.catalogs.extract()
    self.assertEqual(19, len(template_catalog))
    expected = [
        'Hello World!',
        'Hello World 2!',
        'Tagged String',
        'Tagged String in List 1',
        'Tagged String in List 2',
    ]
    for string in expected:
      self.assertIn(string, template_catalog)

  def test_iter(self):
    locales = self.pod.catalogs.list_locales()
    for catalog in self.pod.catalogs:
      self.assertIn(str(catalog.locale), locales)

  def test_get(self):
    self.pod.catalogs.get('de')

  def test_get_template(self):
    template = self.pod.catalogs.get_template()
    self.assertTrue(template.exists)
    template = self.pod.catalogs.get_template('messages.test.pot')
    self.assertFalse(template.exists)
    self.assertEqual(0, len(template))

  def test_compile(self):
    self.pod.catalogs.compile()

  def test_to_message(self):
    self.pod.catalogs.to_message()

#  TODO: Fix, since this currently affects testdata.
#  def test_init(self):
#    self.pod.catalogs.init(['de'])

  def test_update(self):
    self.pod.catalogs.update(['de'])


if __name__ == '__main__':
  unittest.main()
