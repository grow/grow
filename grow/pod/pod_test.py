"""Tests for Grow pod."""

import unittest

from grow.pod import pod
from grow.pod import podspec
from grow.storage import local as grow_local
from grow.testing import storage as test_storage


class PodTest(unittest.TestCase):
    """Grow pod specification testing."""

    def _make_podspec(self, value=''):
        self.storage.write_file(podspec.POD_SPEC_FILE, value)

    def setUp(self):
        self.test_fs = test_storage.TestFileStorage()
        self.storage = grow_local.LocalStorage(self.test_fs.content_dir)

    def test_missing_podspec(self):
        """Podspec missing."""
        with self.assertRaises(pod.MissingPodspecError):
            pod.Pod('/testing', storage=self.storage)

    def test_root_path(self):
        """Pod root path."""
        self._make_podspec()
        test_pod = pod.Pod('/testing', storage=self.storage)
        self.assertEqual('/testing', test_pod.root_path)


if __name__ == '__main__':
    unittest.main()
