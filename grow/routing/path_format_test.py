"""Tests for the path formatter."""

import datetime
import unittest
from grow.testing import mocks
from grow.routing import path_format as grow_path_format


class PathFormatTestCase(unittest.TestCase):
    """Test the routes."""

    def test_format_doc_root(self):
        """Test doc paths."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = mocks.mock_doc(pod)
        self.assertEquals(
            '/root_path/test/', path_format.format_doc(doc, '/{root}/test'))

    def test_format_doc_base(self):
        """Test doc base."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        collection = mocks.mock_collection(basename='/pages/')
        doc = mocks.mock_doc(pod, base='jump', collection=collection,
                        collection_base_path='/sub/')
        self.assertEquals(
            '/root_path/jump/test/',
            path_format.format_doc(doc, '/{root}/{base}/test'))

    def test_format_doc_base_lower(self):
        """Test doc base with lower filter."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        collection = mocks.mock_collection(basename='/pages/')
        doc = mocks.mock_doc(pod, base='JUMP', collection=collection,
                        collection_base_path='/sub/')
        self.assertEquals(
            '/root_path/jump/test/',
            path_format.format_doc(doc, '/{root}/{base|lower}/test'))

    def test_format_doc_collection(self):
        """Test doc paths."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        collection = mocks.mock_collection(basename='/pages/')
        doc = mocks.mock_doc(pod, collection=collection,
                        collection_base_path='/sub/')
        self.assertEquals(
            '/root_path/sub/test/',
            path_format.format_doc(doc, '/{root}/{collection.base_path}/test'))

    def test_format_doc_date(self):
        """Test doc path with date string."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        collection = mocks.mock_collection(basename='/pages/')
        doc = mocks.mock_doc(pod, date='2018-01-01', collection=collection,
                        collection_base_path='/sub/')
        self.assertEquals(
            '/root_path/2018-01-01/test/',
            path_format.format_doc(doc, '/{root}/{date}/test'))

    def test_format_doc_datetime(self):
        """Test doc path with date string."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        collection = mocks.mock_collection(basename='/pages/')
        doc_date = datetime.datetime(2019, 2, 3)
        doc = mocks.mock_doc(pod, date=doc_date, collection=collection,
                        collection_base_path='/sub/')
        self.assertEquals(
            '/root_path/2019-02-03/test/',
            path_format.format_doc(doc, '/{root}/{date}/test'))

    def test_format_doc_locale(self):
        """Test doc paths with locale."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = mocks.mock_doc(pod, locale='es')
        self.assertEquals(
            '/root_path/test/es/', path_format.format_doc(
                doc, '/{root}/test/{locale}'))

    def test_format_doc_locale_alias(self):
        """Test doc paths with locale."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        locale = mocks.mock_locale('es', 'es_us')
        path_format = grow_path_format.PathFormat(pod)
        doc = mocks.mock_doc(pod, locale=locale)
        self.assertEquals(
            '/root_path/test/es_us/', path_format.format_doc(
                doc, '/{root}/test/{locale}'))

    def test_format_doc_locale_params(self):
        """Test doc paths with locale and keeping params."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = mocks.mock_doc(pod, locale='es')
        self.assertEquals(
            '/root_path/test/:locale/', path_format.format_doc(
                doc, '/{root}/test/{locale}', parameterize=True))

    def test_format_pod_root(self):
        """Test pod paths."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test', path_format.format_pod('/{root}/test'))

    def test_format_pod_env_fingerprint(self):
        """Test env fingerprints."""
        env = mocks.mock_env(fingerprint="ABC123")
        pod = mocks.mock_pod(env=env)
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/ABC123/test', path_format.format_pod('/{env.fingerprint}/test'))

    def test_format_pod_extra_slash(self):
        """Test extra slashes are removed."""
        pod = mocks.mock_pod(podspec={
            'root': '/root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test', path_format.format_pod('/{root}/test'))

    def test_format_pod_params(self):
        """Test params are converted."""
        pod = mocks.mock_pod(podspec={
            'root': '/root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test/:locale/something',
            path_format.format_pod(
                '/{root}/test/{locale}/something', parameterize=True))

    def test_format_static_root(self):
        """Test doc paths."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test', path_format.format_static('/{root}/test'))

    def test_format_static_locale(self):
        """Test doc paths with locale."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test/es', path_format.format_static(
                '/{root}/test/{locale}', locale='es'))

    def test_format_static_locale_params(self):
        """Test doc paths with locale and keeping params."""
        pod = mocks.mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test/:locale', path_format.format_static(
                '/{root}/test/{locale}', locale='es', parameterize=True))

    def test_parameterize(self):
        """Test parameters are converted."""
        path = grow_path_format.PathFormat.parameterize('/{root}')
        self.assertEquals('/:root', path)

        path = grow_path_format.PathFormat.parameterize('/{root}/test')
        self.assertEquals('/:root/test', path)

        path = grow_path_format.PathFormat.parameterize('/{root}/{test}')
        self.assertEquals('/:root/:test', path)

    def test_parameterize_section(self):
        """Test parameters are only converted for a complete section."""
        path = grow_path_format.PathFormat.parameterize('/{root}/{test}.jpg')
        self.assertEquals('/:root/{test}.jpg', path)

        path = grow_path_format.PathFormat.parameterize(
            '/{root}/something.{test}')
        self.assertEquals('/:root/something.{test}', path)

    def test_trailing_slash(self):
        """Slashes are added for html files if they are missing."""
        pod = mocks.mock_pod()
        doc = mocks.mock_doc(pod, view='/view/base.html')
        self.assertEquals(
            '/', grow_path_format.PathFormat.trailing_slash(doc, '/'))
        self.assertEquals(
            '/foo/bar/', grow_path_format.PathFormat.trailing_slash(doc, '/foo/bar'))
        self.assertEquals(
            '/foo/bar/', grow_path_format.PathFormat.trailing_slash(doc, '/foo/bar/'))

        # Doesn't add for non-html views.
        doc = mocks.mock_doc(pod, view='/view/base.xml')
        self.assertEquals(
            '/foo/bar', grow_path_format.PathFormat.trailing_slash(doc, '/foo/bar'))


if __name__ == '__main__':
    unittest.main()
