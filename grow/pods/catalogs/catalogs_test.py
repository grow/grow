from grow.pods import pods
from grow.pods import storage
import unittest


class CatalogTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_to_message(self):
    de_catalog = self.pod.catalogs.get('de')
    de_catalog.to_message()

  def test_gettext_translations(self):
    de_catalog = self.pod.catalogs.get('de')
    de_catalog.gettext_translations

#  TODO: Fix, since this currently affects testdata.
#  def test_init(self):
#    de_catalog = self.pod.catalogs.get('de')
#    de_catalog.init()

  def test_update(self):
    de_catalog = self.pod.catalogs.get('de')
    de_catalog.update()

  def test_exists(self):
    de_catalog = self.pod.catalogs.get('de')
    self.assertTrue(de_catalog.exists)
    da_catalog = self.pod.catalogs.get('da')
    self.assertFalse(da_catalog.exists)

  def test_compile(self):
    de_catalog = self.pod.catalogs.get('de')
    de_catalog.compile()

  def test_in(self):
    de_catalog = self.pod.catalogs.get('de')
    self.assertIn('AboutDE', de_catalog)
    self.assertEqual(18, len(de_catalog))

  def test_save(self):
    it_catalog = self.pod.catalogs.get('it')
    self.assertNotIn('foo', it_catalog)
    it_catalog.add('foo', 'bar')
    it_catalog.save()

    it_catalog = self.pod.catalogs.get('it')
    self.assertIn('foo', it_catalog)
    it_catalog.delete('foo')
    it_catalog.save()

    it_catalog = self.pod.catalogs.get('it')
    self.assertNotIn('foo', it_catalog)


if __name__ == '__main__':
  unittest.main()
