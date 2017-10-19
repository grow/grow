"""Tests for the router."""

import unittest
from grow.pods import pods
from grow.pods import storage
from grow.routing import router as grow_router
from grow.testing import testing


class RoutesTestCase(unittest.TestCase):
    """Test the router."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.router = grow_router.Router(self.pod)

    def test_router(self):
        """."""
        pass


if __name__ == '__main__':
    unittest.main()
