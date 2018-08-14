"""Tests for Grow pod."""

import unittest

from grow.pod import pod


class PodTest(unittest.TestCase):
    """Grow pod specification testing."""

    def test_root_path(self):
        """Pod root path."""
        test_pod = pod.Pod('/testing')
        self.assertEqual('/testing', test_pod.root_path)


if __name__ == '__main__':
    unittest.main()
