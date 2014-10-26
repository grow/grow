from grow.pods import pods
from grow.pods import storage
import unittest


class TranslationsTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_list_locales(self):
    self.assertListEqual(
        ['fr', 'de', 'en', 'it', 'ja'],
        self.pod.translations.list_locales())

  def test_extract(self):
    catalog = self.pod.translations.extract()
    self.assertEqual(14, len(catalog))  # X from views, N from content.
    expected = [
        'Hello World!',
        'Hello World 2!',
    ]
    for string in expected:
      self.assertTrue(catalog.get(string))

  def test_recompile_mo_files(self):
    self.pod.translations.recompile_mo_files()

  def test_get_catalog(self):
    catalog = self.pod.translations.get_catalog()
    for message in catalog:
      message


class TranslationTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

#  def test_to_message(self):
#    translation = self.pod.translations.get_translation('de')
#    translation.to_message()


if __name__ == '__main__':
  unittest.main()
