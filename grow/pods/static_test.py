"""Tests for the static file object."""

import textwrap
import unittest
from grow.common import utils
from grow.pods import pods
from grow import storage
from grow.testing import testing
from . import static


class StaticTest(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_static(self):
        static = self.pod.get_static('/static/test.txt')
        self.assertEqual('/app/static/test-db3f6eaa28bac5ae1180257da33115d8.txt', static.url.path)
        static_de = self.pod.get_static('/static/test.txt', locale='de')
        self.assertEqual('/app/root/static/somepath/de_alias/test-9b3051eb0c19358847e7c879275f810a.txt',
                         static_de.url.path)
        static_same = self.pod.get_static('/static/test.txt')
        self.assertEqual(static, static_same)
        self.assertNotEqual(static, static_de)
        self.assertEqual('test', static.base)
        self.assertIsNotNone(static.modified)
        self.assertTrue(static.exists)
        self.assertEqual('.txt', static.ext)
        static = self.pod.get_static('/static/file with spaces.txt')
        path = '/app/static/file with spaces-d41d8cd98f00b204e9800998ecf8427e.txt'
        self.assertEqual(path, static.url.path)

        fingerprint = '961109f2e6cc139a8f6df6e3a307c247'
        static = self.pod.get_static(
            '/static-fingerprint/fingerprinted.txt')
        self.assertEqual(
            '/root/static-fingerprint/{}/fingerprinted.txt'.format(fingerprint),
            static.url.path)
        static = self.pod.get_static(
            '/static-fingerprint/fingerprinted.txt', locale='de')
        fingerprint = 'bc20b3c9007842b8e1f3c640b07f4e74'
        self.assertEqual(
            '/root/static-fingerprint/{}/de_alias/fingerprinted.txt'.format(fingerprint),
            static.url.path)

    def test_apply_fingerprint(self):
        fingerprint = 'bc20b3c9007842b8e1f3c640b07f4e74'
        path = '/path-path/file.txt'
        expected = '/path-path/file-{}.txt'.format(fingerprint)
        self.assertEqual(expected, static.StaticFile.apply_fingerprint(path, fingerprint))
        path = '/path-path/file.min.js'
        expected = '/path-path/file-{}.min.js'.format(fingerprint)
        self.assertEqual(expected, static.StaticFile.apply_fingerprint(path, fingerprint))

    def test_remove_fingerprint(self):
        fingerprint = 'bc20b3c9007842b8e1f3c640b07f4e74'
        path = '/path-path/file-{}.txt'.format(fingerprint)
        expected = '/path-path/file.txt'
        self.assertEqual(expected, static.StaticFile.remove_fingerprint(path))
        path = '/path-path/file-{}.min.js'.format(fingerprint)
        expected = '/path-path/file.min.js'
        self.assertEqual(expected, static.StaticFile.remove_fingerprint(path))

    # TODO: Failing on GAE tests?
    # def test_yaml_dump(self):
    #     """Test if the yaml representer is working correctly."""
    #     static_file = self.pod.get_static('/static/test.txt')
    #     input_obj = {
    #         'static': static_file
    #     }
    #     expected = textwrap.dedent(
    #         """\
    #         static: !g.static '/static/test.txt'
    #         """)
    #     self.assertEqual(expected, utils.dump_yaml(input_obj))


if __name__ == '__main__':
    unittest.main()
