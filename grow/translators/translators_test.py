from . import google_translator_toolkit
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class TranslatorTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_upload_translations(self):
        translator = self.pod.get_translator('gtt')
        translator.upload(locales=['de'])


if __name__ == '__main__':
    unittest.main()
