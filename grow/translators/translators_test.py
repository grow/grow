from . import google_translator_toolkit
from grow.preprocessors import google_drive
from grow.common import oauth
from grow.pods import pods
from grow import storage
from nose.plugins import skip
from grow.testing import testing
import time
import unittest


class TranslatorTestCase(testing.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        super(TranslatorTestCase, self).setUp()

    def test_upload_and_download_sheets_translations(self):
        translator = self.pod.get_translator('google_translator_toolkit')
        credentials, _ = oauth.get_credentials_and_storage(
            scope=google_drive.OAUTH_SCOPE,
            storage_key=google_drive.STORAGE_KEY)
        if not credentials:
            text = ('Skipping Google Sheets Translator test'
                    ' because we don\'t have auth keys. Run'
                    ' `grow upload_translations` or `grow download_translations`'
                    ' to acquire auth keys and re-run the test.')
            raise skip.SkipTest(text)
        translator.upload(locales=['de'])
        translator.download(locales=['de'])

    def test_upload_and_download_gtt_translations(self):
        self.assertRaises(ValueError, self.pod.get_translator, 'gtt')
        translator = self.pod.get_translator('google_translator_toolkit')
        credentials, _ = oauth.get_credentials_and_storage(
            scope=google_translator_toolkit.OAUTH_SCOPE,
            storage_key=google_translator_toolkit.STORAGE_KEY)
        if not credentials:
            text = ('Skipping Google Translator Toolkit test'
                    ' because we don\'t have auth keys. Run'
                    ' `grow upload_translations` or `grow download_translations`'
                    ' to acquire auth keys and re-run the test.')
            raise skip.SkipTest(text)
        translator.upload(locales=['de'])
        time.sleep(2)  # Wait for the document to be ready in GTT.
        translator.download(locales=['de'])
        translator.update_acl()
        translator.update_acl(locales=['de'])


if __name__ == '__main__':
    unittest.main()
