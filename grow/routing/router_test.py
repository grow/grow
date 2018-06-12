"""Tests for the router."""

import unittest
from grow.routing import router as grow_router
from grow.routing import routes as grow_routes
from grow.testing import mocks


class RouterTestCase(unittest.TestCase):
    """Test the router."""

    def setUp(self):
        self.router = grow_router.Router()

    def test_add_doc(self):
        """Adding docs changes the routes length."""
        doc = mocks.mock_doc(serving_path='/foo')
        self.router.add_doc(doc)
        self.assertEqual(1, len(self.router.routes))

        # Docs without serving_path ignored.
        doc = mocks.mock_doc()
        self.router.add_doc(doc)
        self.assertEqual(1, len(self.router.routes))

    def test_add_static_doc(self):
        """Adding docs changes the routes length."""
        doc = mocks.mock_static_doc(serving_path='/foo')
        self.router.add_static_doc(doc)
        self.assertEqual(1, len(self.router.routes))

        # Docs without serving_path ignored.
        doc = mocks.mock_static_doc(serving_path='')
        self.router.add_static_doc(doc)
        self.assertEqual(1, len(self.router.routes))

    def test_filter(self):
        """Filtering by locale reduces routes."""
        doc = mocks.mock_doc(serving_path='/foo', locale='en')
        self.router.add_doc(doc)
        doc = mocks.mock_doc(serving_path='/bar', locale='es')
        self.router.add_doc(doc)
        doc = mocks.mock_doc(serving_path='/baz', locale='fr')
        self.router.add_doc(doc)
        self.assertEqual(3, len(self.router.routes))
        self.router.filter(locales=('es',))
        self.assertEqual(1, len(self.router.routes))

    def test_filter_multi(self):
        """Filtering by multiple locales reduces routes."""
        doc = mocks.mock_doc(serving_path='/foo', locale='en')
        self.router.add_doc(doc)
        doc = mocks.mock_doc(serving_path='/bar', locale='es')
        self.router.add_doc(doc)
        doc = mocks.mock_doc(serving_path='/baz', locale='fr')
        self.router.add_doc(doc)
        self.assertEqual(3, len(self.router.routes))
        self.router.filter(locales=('es', 'fr'))
        self.assertEqual(2, len(self.router.routes))

    def test_reconcile_docs(self):
        """Reconciles the documents."""
        doc = mocks.mock_doc(serving_path='/foo')
        self.router.add_doc(doc)
        self.assertEqual(1, len(self.router.routes))

        old_docs = [doc]
        new_docs = [
            mocks.mock_doc(serving_path='/bar'),
            mocks.mock_doc(serving_path='/foobar'),
        ]

        self.router.reconcile_documents(
            remove_docs=old_docs, add_docs=new_docs)

        self.assertEqual(2, len(self.router.routes))

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


class RouteInfoTestCase(unittest.TestCase):
    """Test the route info."""

    def test_eq(self):
        """Route info are equal."""
        info = grow_router.RouteInfo('doc', meta={'testing': True})
        info2 = grow_router.RouteInfo('doc', meta={'testing': True})
        self.assertTrue(info == info2)

    def test_neq(self):
        """Route info are not equal."""
        info = grow_router.RouteInfo('doc', meta={'testing': True})
        info2 = grow_router.RouteInfo('doc', meta={'testing': False})
        self.assertTrue(info != info2)

    def test_repr(self):
        """Route info repr."""
        info = grow_router.RouteInfo('doc', meta={'testing': True})
        self.assertEqual(
            '<RouteInfo kind=doc meta={\'testing\': True}>', repr(info))


if __name__ == '__main__':
    unittest.main()
