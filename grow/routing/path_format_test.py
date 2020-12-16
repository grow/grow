"""Tests for the path formatter."""

import unittest
import mock
from grow.routing import path_format as grow_path_format


def _mock_collection(basename=None, root=None):
    collection = mock.Mock()
    type(collection).basename = mock.PropertyMock(return_value=basename)
    type(collection).root = mock.PropertyMock(return_value=root)
    return collection


def _mock_env(fingerprint=None):
    env = mock.Mock()
    prop_fingerprint = mock.PropertyMock(return_value=fingerprint)
    type(env).fingerprint = prop_fingerprint
    return env


def _mock_pod(podspec=None, env=None):
    pod = mock.Mock()
    mock_podspec = mock.Mock()
    if not podspec:
        podspec = {}
    mock_podspec.get_config.return_value = podspec
    type(pod).podspec = mock.PropertyMock(return_value=mock_podspec)
    if not env:
        env = _mock_env()
    type(pod).env = mock.PropertyMock(return_value=env)
    return pod


def _mock_doc(pod, base=None, locale=None, collection_base_path=None, collection=None, view=None):
    doc = mock.Mock()
    type(doc).pod = mock.PropertyMock(return_value=pod)
    type(doc).base = mock.PropertyMock(return_value=base)
    type(doc).locale = mock.PropertyMock(return_value=locale)
    if not collection:
        collection = _mock_collection()
    type(doc).collection = mock.PropertyMock(return_value=collection)
    type(doc).collection_base_path = mock.PropertyMock(return_value=collection_base_path)
    type(doc).view = mock.PropertyMock(return_value=view or '/view/base.html')
    return doc


def _mock_static(pod, path_format, locale=None):
    doc = mock.Mock()
    type(doc).pod = mock.PropertyMock(return_value=pod)
    type(doc).path_format = mock.PropertyMock(return_value=path_format)
    type(doc).locale = mock.PropertyMock(return_value=locale)
    return doc


class PathFormatTestCase(unittest.TestCase):
    """Test the routes."""

    def test_format_doc_base(self):
        """Test doc paths with the base filename."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = _mock_doc(pod, base='doc1')
        self.assertEqual(
            '/doc1/', path_format.format_doc(doc, '/{base}/'))

    def test_format_doc_base_index(self):
        """Test doc paths with the index as a base filename."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = _mock_doc(pod, base='index')
        self.assertEqual(
            '/', path_format.format_doc(doc, '/{base}/'))
        self.assertEqual(
            '/', path_format.format_doc(doc, '/{base}'))

        # Does not replace index when it is not the end of the path.
        self.assertEqual(
            '/index.html', path_format.format_doc(doc, '/{base}.html'))

    def test_format_doc_root(self):
        """Test doc paths."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = _mock_doc(pod)
        self.assertEqual(
            '/root_path/test/', path_format.format_doc(doc, '/{root}/test'))

    def test_format_doc_collection(self):
        """Test doc paths."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        collection = _mock_collection(basename='/pages/')
        doc = _mock_doc(pod, collection=collection, collection_base_path='/sub/')
        self.assertEqual(
            '/root_path/sub/test/',
            path_format.format_doc(doc, '/{root}/{collection.base_path}/test'))

    def test_format_doc_locale(self):
        """Test doc paths with locale."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = _mock_doc(pod, locale='es')
        self.assertEqual(
            '/root_path/test/es/', path_format.format_doc(
                doc, '/{root}/test/{locale}'))

    def test_format_doc_locale_params(self):
        """Test doc paths with locale and keeping params."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        doc = _mock_doc(pod, locale='es')
        self.assertEqual(
            '/root_path/test/:locale/', path_format.format_doc(
                doc, '/{root}/test/{locale}', parameterize=True))

    def test_format_pod_root(self):
        """Test pod paths."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/root_path/test', path_format.format_pod('/{root}/test'))

    def test_format_pod_env_fingerprint(self):
        """Test env fingerprints."""
        env = _mock_env(fingerprint="ABC123")
        pod = _mock_pod(env=env)
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/ABC123/test', path_format.format_pod('/{env.fingerprint}/test'))

    def test_format_pod_extra_slash(self):
        """Test extra slashes are removed."""
        pod = _mock_pod(podspec={
            'root': '/root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/root_path/test', path_format.format_pod('/{root}/test'))

    def test_format_pod_params(self):
        """Test params are converted."""
        pod = _mock_pod(podspec={
            'root': '/root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/root_path/test/:locale/something',
            path_format.format_pod(
                '/{root}/test/{locale}/something', parameterize=True))

    def test_format_static_root(self):
        """Test doc paths."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/root_path/test', path_format.format_static('/{root}/test'))

    def test_format_static_locale(self):
        """Test doc paths with locale."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/root_path/test/es', path_format.format_static(
                '/{root}/test/{locale}', locale='es'))

    def test_format_static_fingerprint(self):
        """Test doc paths with fingerprint."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/root_path/test/asdf', path_format.format_static(
                '/{root}/test/{fingerprint}', fingerprint='asdf'))

    def test_format_static_locale_params(self):
        """Test doc paths with locale and keeping params."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEqual(
            '/root_path/test/:locale', path_format.format_static(
                '/{root}/test/{locale}', locale='es', parameterize=True))

    def test_parameterize(self):
        """Test parameters are converted."""
        path = grow_path_format.PathFormat.parameterize('/{root}')
        self.assertEqual('/:root', path)

        path = grow_path_format.PathFormat.parameterize('/{root}/test')
        self.assertEqual('/:root/test', path)

        path = grow_path_format.PathFormat.parameterize('/{root}/{test}')
        self.assertEqual('/:root/:test', path)

    def test_parameterize_section(self):
        """Test parameters are only converted for a complete section."""
        path = grow_path_format.PathFormat.parameterize('/{root}/{test}.jpg')
        self.assertEqual('/:root/{test}.jpg', path)

        path = grow_path_format.PathFormat.parameterize(
            '/{root}/something.{test}')
        self.assertEqual('/:root/something.{test}', path)

    def test_trailing_slash(self):
        """Slashes are added for html files if they are missing."""
        pod = _mock_pod()
        doc = _mock_doc(pod, view='/view/base.html')
        self.assertEqual('/', grow_path_format.PathFormat.trailing_slash(doc, '/'))
        self.assertEqual('/foo/bar/', grow_path_format.PathFormat.trailing_slash(doc, '/foo/bar'))
        self.assertEqual('/foo/bar/', grow_path_format.PathFormat.trailing_slash(doc, '/foo/bar/'))

        # Doesn't add for non-html views.
        doc = _mock_doc(pod, view='/view/base.xml')
        self.assertEqual('/foo/bar', grow_path_format.PathFormat.trailing_slash(doc, '/foo/bar'))

    def test_trailing_slash_path(self):
        """Slashes are not added for paths with a common extension."""
        pod = _mock_pod()
        doc = _mock_doc(pod)
        self.assertEqual('/', grow_path_format.PathFormat.trailing_slash(doc, '/'))
        self.assertEqual('/bar.html', grow_path_format.PathFormat.trailing_slash(doc, '/bar.html'))
        self.assertEqual('/bar.htm', grow_path_format.PathFormat.trailing_slash(doc, '/bar.htm'))
        self.assertEqual('/bar.xml', grow_path_format.PathFormat.trailing_slash(doc, '/bar.xml'))
        self.assertEqual('/bar.svg', grow_path_format.PathFormat.trailing_slash(doc, '/bar.svg'))

        # Not all extensions are supported for docs.
        self.assertEqual('/bar.png/', grow_path_format.PathFormat.trailing_slash(doc, '/bar.png'))


if __name__ == '__main__':
    unittest.main()
