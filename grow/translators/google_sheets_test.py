from . import google_translator_toolkit
from grow.preprocessors import google_drive
from grow.common import oauth
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
from nose.plugins import skip
import time
import unittest


class GoogleSheetsTranslatorTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_upload_translations(self):
        credentials, _ = oauth.get_credentials_and_storage(
            scope=google_drive.OAUTH_SCOPE,
            storage_key=google_drive.STORAGE_KEY)
        if not credentials:
            text = ('Skipping Google Sheets Translator test'
                    ' because we don\'t have auth keys. Run'
                    ' `grow upload_translations` or `grow download_translations`'
                    ' to acquire auth keys and re-run the test.')
            raise skip.SkipTest(text)
        translator = self.pod.get_translator('google_sheets')
        translator.upload(locales=['de'])


if __name__ == '__main__':
    unittest.main()
