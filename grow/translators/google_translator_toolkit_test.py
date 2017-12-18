from . import google_translator_toolkit
from grow.common import oauth
from grow.pods import pods
from grow import storage
from grow.testing import testing
from nose.plugins import skip
import time
import unittest


class GoogleTranslatorToolkitTestCase(testing.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        super(GoogleTranslatorToolkitTestCase, self).setUp()

    def test_insert_document(self):
        catalog = self.pod.catalogs.get('de')
        content = catalog.content
        mimetype = 'text/x-gettext-translation'
        source_lang = 'en'
        lang = str(catalog.locale)
        name = 'Test Display Name'
        credentials, _ = oauth.get_credentials_and_storage(
            scope=google_translator_toolkit.OAUTH_SCOPE,
            storage_key=google_translator_toolkit.STORAGE_KEY)
        if not credentials:
            text = ('Skipping Google Translator Toolkit test'
                    ' because we don\'t have auth keys. Run'
                    ' `grow upload_translations` or `grow download_translations`'
                    ' to acquire auth keys and re-run the test.')
            raise skip.SkipTest(text)
        gtt = google_translator_toolkit.Gtt()
        insert_resp = gtt.insert_document(
            name=name,
            content=content,
            source_lang=source_lang,
            lang=lang,
            mimetype=mimetype)
        document_id = insert_resp['id']
        time.sleep(2)  # Wait for the document to be ready in GTT.
        download_resp = gtt.download_document(document_id)


if __name__ == '__main__':
    unittest.main()
