"""Tests for urls."""

import unittest
from grow.pods import pods
from grow.testing import testing
from . import urls


class UrlTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path)

    def test_relative_path(self):
        """Relative paths."""
        relative_path = urls.Url.create_relative_path(
            '/foo/bar/baz/', relative_to='/test/dir/')
        self.assertEqual('../../foo/bar/baz/', relative_path)

        relative_path = urls.Url.create_relative_path(
            '/foo/bar/baz/', relative_to='/test/dir/foo/')
        self.assertEqual('../../../foo/bar/baz/', relative_path)

        relative_path = urls.Url.create_relative_path(
            '/', relative_to='/test/dir/foo/')
        self.assertEqual('../../../', relative_path)

        relative_path = urls.Url.create_relative_path(
            '/foo/bar/', relative_to='/')
        self.assertEqual('./foo/bar/', relative_path)

        relative_path = urls.Url.create_relative_path(
            '/foo/bar/', relative_to='/foo/')
        self.assertEqual('./bar/', relative_path)

        relative_path = urls.Url.create_relative_path(
            'http://www.example.com/', relative_to='/foo/')
        self.assertEqual('http://www.example.com/', relative_path)

        relative_path = urls.Url.create_relative_path(
            'https://www.example.com/', relative_to='/foo/')
        self.assertEqual('https://www.example.com/', relative_path)

        url = urls.Url('/foo/')
        relative_path = urls.Url.create_relative_path(
            url, relative_to='/foo/')
        self.assertEqual('./', relative_path)

        url = urls.Url('/foo/test.html')
        relative_path = urls.Url.create_relative_path(
            url, relative_to='/foo/')
        self.assertEqual('./test.html', relative_path)

        url = urls.Url('/test.html')
        relative_path = urls.Url.create_relative_path(
            url, relative_to='/foo/')
        self.assertEqual('../test.html', relative_path)

    def test_relative_path_ext(self):
        """Relative paths with extensions."""
        relative_path = urls.Url.create_relative_path(
            '/foo.html', relative_to='/bar.html')
        self.assertEqual('./foo.html', relative_path)

        relative_path = urls.Url.create_relative_path(
            '/foo/bar.html', relative_to='/bar.html')
        self.assertEqual('./foo/bar.html', relative_path)

        relative_path = urls.Url.create_relative_path(
            '/bar.html', relative_to='/foo/bar.html')
        self.assertEqual('../bar.html', relative_path)

    def test_relative_path_ext_dir(self):
        """Relative paths with extensions and directories mixed."""
        relative_path = urls.Url.create_relative_path(
            '/bar/', relative_to='/foo/bar.html')
        self.assertEqual('../bar/', relative_path)

        relative_path = urls.Url.create_relative_path(
            '/bar.html', relative_to='/foo/')
        self.assertEqual('../bar.html', relative_path)

    def test_scheme_and_port(self):
        """Scheme and port combinations."""
        url = urls.Url('/', host='grow.io')
        self.assertEqual('http://grow.io/', str(url))

        url = urls.Url('/', host='grow.io', scheme='https')
        self.assertEqual('https://grow.io/', str(url))

        url = urls.Url('/', host='grow.io', port=8080)
        self.assertEqual('http://grow.io:8080/', str(url))

        url = urls.Url('/', host='grow.io', port=8080, scheme='https')
        self.assertEqual('https://grow.io:8080/', str(url))

        url = urls.Url('/', host='grow.io', port=443)
        self.assertEqual('https://grow.io/', str(url))

        url = urls.Url('/', host='grow.io', port=80)
        self.assertEqual('http://grow.io/', str(url))

        url = urls.Url('/', host='grow.io', scheme='http')
        self.assertEqual('http://grow.io/', str(url))

        url = urls.Url('/', host='grow.io', scheme='http', port=443)
        self.assertEqual('http://grow.io:443/', str(url))


if __name__ == '__main__':
    unittest.main()
