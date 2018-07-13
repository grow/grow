"""Tests for importers."""

import os
import unittest
from grow.pods import pods
from grow import storage
from grow.testing import testing


class ImportersTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.pod.catalogs.compile()

    def test_import_path_with_po_file(self):
        de_catalog = self.pod.catalogs.get('de')
        self.assertIn('About', de_catalog)
        self.assertNotIn('German Translation', de_catalog)

        path = testing.get_testdata_dir()
        po_path_to_import = os.path.join(path, 'external', 'messages.de.po')
        self.pod.catalogs.import_translations(po_path_to_import, locale='de')
        de_catalog = self.pod.catalogs.get('de')
        self.assertIn('German Translation', de_catalog)
        # Verify strings not present in the catalog-to-merge are preserved
        # in the existing catalog.
        self.assertIn('About', de_catalog)

    def test_import_path_with_zip_file(self):
        de_catalog = self.pod.catalogs.get('de')
        self.assertNotIn('German Translation', de_catalog)

        path = testing.get_testdata_dir()
        po_path_to_import = os.path.join(path, 'external', 'messages.de.zip')
        self.pod.catalogs.import_translations(po_path_to_import)
        de_catalog = self.pod.catalogs.get('de')
        self.assertIn('German Translation', de_catalog)

    def test_import_path_with_zip_file_and_identifier_mapping(self):
        de_catalog = self.pod.catalogs.get('de')
        self.assertNotIn('German Translation', de_catalog)

        path = testing.get_testdata_dir()
        po_path_to_import = os.path.join(path, 'external', 'messages.de_DE.zip')
        self.pod.catalogs.import_translations(po_path_to_import)
        de_catalog = self.pod.catalogs.get('de')
        self.assertIn('German Translation', de_catalog)

    def test_import_csv(self):
        de_catalog = self.pod.catalogs.get('de')
        self.assertNotIn('German Translation', de_catalog)
        self.assertNotIn('Hello World', de_catalog)

        path = testing.get_testdata_dir()
        po_path_to_import = os.path.join(path, 'external', 'messages.csv')
        self.pod.catalogs.import_translations(po_path_to_import)
        de_catalog = self.pod.catalogs.get('de')
        self.assertIn('German Translation', de_catalog)
        self.assertIn('Hello World', de_catalog)


if __name__ == '__main__':
    unittest.main()
