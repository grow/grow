"""Tests for the static document."""

import unittest
from grow.documents import static_document
from grow.pods import pods
from grow import storage
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

        static_doc = static_document.StaticDocument(
            self.pod, '/static-a/test-a.txt')
        self.assertTrue(static_doc.exists)

        static_doc = static_document.StaticDocument(
            self.pod, '/static-b/test-a.txt')
        self.assertFalse(static_doc.exists)

    def test_filter(self):
        """Static filter config."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals(static_doc.filter, {})

    def test_path_format(self):
        """Static document path format."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('/app/static/test.txt', static_doc.path_format)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/something.txt')
        self.assertEquals('/app/static/something.txt', static_doc.path_format)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/something.txt', locale='de')
        self.assertEquals(
            '/app/{root}/static/somepath/{locale}/something.txt', static_doc.path_format)

    def test_path_filter(self):
        """Static path filter."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertTrue(static_doc.path_filter.is_valid(static_doc.serving_path))

    def test_serving_path(self):
        """Static document serving path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals(
            '/app/static/test-db3f6eaa28bac5ae1180257da33115d8.txt', static_doc.serving_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt', locale='de')
        self.assertEquals(
            '/app/root/static/somepath/de/test-db3f6eaa28bac5ae1180257da33115d8.txt',
            static_doc.serving_path)

    def test_serving_path_parameterized(self):
        """Static document parameterized serving path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals(
            '/app/static/test.txt', static_doc.serving_path_parameterized)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/something.txt', locale='de')
        self.assertEquals(
            '/app/root/static/somepath/:locale/something.txt',
            static_doc.serving_path_parameterized)

    def test_source_path(self):
        """Static document source path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('/static/', static_doc.source_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/something.txt', locale='de')
        self.assertEquals('/static/intl/{locale}/', static_doc.source_path)

    def test_source_path_multi_paths(self):
        """Static document source path with multiple source dirs."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static-a/test-a.txt')
        self.assertEquals('/static-a/', static_doc.source_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static-b/test-b.txt')
        self.assertEquals('/static-b/', static_doc.source_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static-a/test-a.txt', locale='de')
        self.assertEquals('/static-a/intl/{locale}/', static_doc.source_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static-b/test-b.txt', locale='de')
        self.assertEquals('/static-b/intl/{locale}/', static_doc.source_path)

    def test_source_paths(self):
        """Static document source paths."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static-a/test-a.txt')
        self.assertEquals('/static-a/', static_doc.source_path)
        static_doc = static_document.StaticDocument(
            self.pod, '/static-b/test-b.txt')
        self.assertEquals('/static-b/', static_doc.source_path)

    def test_source_pod_path(self):
        """Static document source path."""
        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt')
        self.assertEquals('/static/test.txt', static_doc.source_pod_path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt', locale='de')
        self.assertEquals(
            '/static/intl/de/test.txt', static_doc.source_pod_path)

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
        self.assertEquals(
            '/app/static/test-db3f6eaa28bac5ae1180257da33115d8.txt', static_doc.url.path)

        static_doc = static_document.StaticDocument(
            self.pod, '/static/test.txt', locale='de')
        self.assertEquals(
            '/app/root/static/somepath/de/test-db3f6eaa28bac5ae1180257da33115d8.txt',
            static_doc.url.path)

if __name__ == '__main__':
    unittest.main()
