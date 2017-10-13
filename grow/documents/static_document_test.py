"""Tests for the static document."""

import unittest
from grow.documents import static_document
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing


class StaticDocumentTestCase(unittest.TestCase):
    """Test the static document."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_exists(self):
        """Static document exists?"""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertTrue(static_doc.exists)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/something.txt')
        self.assertFalse(static_doc.exists)

    def test_path_format(self):
        """Static document path format."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('/app/static/test.txt', static_doc.path_format)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/something.txt')
        self.assertEquals('/app/static/something.txt', static_doc.path_format)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/intl/{locale}/something.txt', locale='de')
        self.assertEquals(
            '/app/{root}/static/somepath/{locale}/something.txt', static_doc.path_format)

    def test_serving_path(self):
        """Static document serving path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('/app/static/test.txt', static_doc.serving_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/intl/{locale}/something.txt', locale='de')
        self.assertEquals(
            '/app/root/static/somepath/de/something.txt', static_doc.serving_path)

    def test_serving_path_parameterized(self):
        """Static document parameterized serving path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals(
            '/app/static/test.txt', static_doc.serving_path_parameterized)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/intl/{locale}/something.txt', locale='de')
        self.assertEquals(
            '/app/root/static/somepath/:locale/something.txt',
            static_doc.serving_path_parameterized)

    def test_source_path(self):
        """Static document source path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('/static/', static_doc.source_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/intl/{locale}/something.txt', locale='de')
        self.assertEquals('/static/intl/{locale}/', static_doc.source_path)

    def test_sub_pod_path(self):
        """Static document source path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('test.txt', static_doc.sub_pod_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/something/test.txt')
        self.assertEquals('something/test.txt', static_doc.sub_pod_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/intl/{locale}/something.txt', locale='de')
        self.assertEquals('something.txt', static_doc.sub_pod_path)

    def test_url(self):
        """Static document url."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('/app/static/test.txt', static_doc.url.path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/intl/{locale}/something.txt', locale='de')
        self.assertEquals(
            '/app/root/static/somepath/de/something.txt', static_doc.url.path)

if __name__ == '__main__':
    unittest.main()
