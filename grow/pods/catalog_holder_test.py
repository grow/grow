from grow.pods import pods
from grow.pods import storage
import unittest


class CatalogsTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)
    self.pod.catalogs.compile()

  def test_list_locales(self):
    self.assertItemsEqual(
        ['de', 'fr', 'en', 'it', 'ja'],
        self.pod.catalogs.list_locales())

  def test_extract(self):
    template_catalog = self.pod.catalogs.extract()
    self.assertEqual(17, len(template_catalog))
    expected = [
        'Hello World!',
        'Hello World 2!',
        'Tagged String',
        'Tagged String in List 1',
        'Tagged String in List 2',
    ]
    for string in expected:
      self.assertIn(string, template_catalog)

  def test_get(self):
    de_catalog = self.pod.catalogs.get('de')

  def test_compile(self):
    self.pod.catalogs.compile()

  def test_to_message(self):
    message = self.pod.catalogs.to_message()

#  TODO: Fix, since this currently affects testdata.
#  def test_init(self):
#    self.pod.catalogs.init(['de'])

  def test_update(self):
    self.pod.catalogs.update(['de'])

  def test_get_template(self):
    self.pod.catalogs.get_template()


if __name__ == '__main__':
  unittest.main()
