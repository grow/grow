"""Tests for the render pool."""

import unittest
from grow.pods import pods
from grow import storage
from grow.rendering import render_pool
from grow.testing import testing


class RenderPoolTestCase(unittest.TestCase):
    """Test the render pool."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.pool = render_pool.RenderPool(self.pod)

    def test_render_pool_pool_size(self):
        """Test that the pool size can be changed."""
        self.assertEquals(1, self.pool.pool_size)
        self.pool.pool_size = 3
        self.assertEquals(3, self.pool.pool_size)


if __name__ == '__main__':
    unittest.main()
