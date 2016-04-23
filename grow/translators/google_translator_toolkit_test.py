from . import google_translator_toolkit
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class GoogleTranslatorToolkitTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_insert_document(self):
        catalog = self.pod.catalogs.get('de')
        content = catalog.content
        mimetype = 'text/x-gettext-translation'
        source_lang = 'en'
        lang = str(catalog.locale)
        name = 'Test Display Name'
        gtt = google_translator_toolkit.Gtt()
        insert_resp = gtt.insert_document(
            name=name,
            content=content,
            source_lang=source_lang,
            lang=lang,
            mimetype=mimetype)
        print insert_resp
        document_id = insert_resp['id']
        # TODO: Attempts to download the document immediately result in a 500.
        import time
        time.sleep(5)
        download_resp = gtt.download_document(document_id)
        print download_resp


if __name__ == '__main__':
    unittest.main()
