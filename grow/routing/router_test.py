"""Tests for the router."""

import unittest
from grow.pods import pods
from grow import storage
from grow.routing import router as grow_router
from grow.testing import testing


class RouterTestCase(unittest.TestCase):
    """Test the router."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage, use_reroute=True)
        self.router = grow_router.Router(self.pod)

    def test_filter(self):
        """Filtering reduces routes."""
        self.router.add_all()
        original_len = len(self.router.routes)
        self.router.filter(locales=['en'])
        modified_len = len(self.router.routes)
        self.assertTrue(modified_len < original_len)


if __name__ == '__main__':
    unittest.main()
