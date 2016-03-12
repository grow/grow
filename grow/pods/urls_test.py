from . import urls
from grow.pods import pods
from grow.testing import testing
import os
import unittest


class UrlTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path)

    def test_relative_path(self):
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


if __name__ == '__main__':
    unittest.main()
