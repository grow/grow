from grow.pods import pods
from grow.pods import storage
import unittest


class TranslationsTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/',
                        storage=storage.FileStorage)

  def test_list_locales(self):
    self.assertListEqual(
        ['de', 'en', 'ja'],
        self.pod.translations.list_locales())

  def test_extract(self):
    self.pod.translations.extract()

  def test_recompile_mo_files(self):
    self.pod.translations.recompile_mo_files()

#  def test_get_catalog(self):
#    self.assertEqual({}, self.pod.translations.get_catalog())


class TranslationTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/',
                        storage=storage.FileStorage)

  def test_to_message(self):
    translation = self.pod.translations.get_translation('de')
    translation.to_message()



if __name__ == '__main__':
  unittest.main()
