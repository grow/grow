"""Tests for the router."""

import unittest
from grow.routing import router as grow_router


class RoutesTestCase(unittest.TestCase):
    """Test the router."""

    def setUp(self):
        self.router = grow_router.Router()

    def test_router(self):
        """."""
        pass


if __name__ == '__main__':
    unittest.main()
