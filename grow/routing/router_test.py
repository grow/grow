"""Tests for the router."""

import unittest
from grow.routing import router as grow_router
from grow.routing import routes as grow_routes
from grow.testing import mocks


class RouterTestCase(unittest.TestCase):
    """Test the router."""

    def setUp(self):
        self.router = grow_router.Router()

    def test_filter(self):
        """Filtering reduces routes."""
        # TODO: Add router tests.
        pass

    def test_simple_routes(self):
        """Can simplify into a simple routes object."""
        doc = mocks.mock_doc(serving_path='/foo')
        self.router.add_doc(doc)
        self.assertEqual(1, len(self.router.routes))
        self.assertTrue(isinstance(self.router.routes, grow_routes.Routes))
        self.router.use_simple()

        # Make sure that the class changes and the routes carry over.
        self.assertEqual(1, len(self.router.routes))
        self.assertTrue(isinstance(self.router.routes, grow_routes.RoutesSimple))


if __name__ == '__main__':
    unittest.main()
