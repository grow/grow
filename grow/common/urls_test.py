"""Tests for urls."""

import unittest
from . import urls


class UrlTest(unittest.TestCase):

    def test_eq(self):
        """URLs equal?"""
        url = urls.Url('/', host='grow.io')
        url2 = urls.Url('/', host='grow.io')
        self.assertTrue(url == url2)

        url = urls.Url('/', host='grow.io')
        url2 = urls.Url('/path', host='grow.io')
        self.assertFalse(url == url2)

        url = urls.Url('/', host='grow.io')
        url2 = urls.Url('/', host='grow.io', port=8080)
        self.assertFalse(url == url2)

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

    def test_repr(self):
        """URL repr."""
        url = urls.Url('/', host='grow.io')
        self.assertEqual('<Url: http://grow.io/>', repr(url))

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
