"""Tests for the routes."""

import unittest
from grow.routing import routes as grow_routes


class DummyDoc(object):
    """Dummy document for testing the routes."""

    def __init__(self, path, pod_path=None, locale=None):
        self.path = path
        self.pod_path = pod_path
        self.locale = locale

    def get_serving_path(self):
        """Get the path it was created with."""
        return self.path


class RoutesTestCase(unittest.TestCase):
    """Test the routes."""

    def _add_doc(self, custom_routes=None, *args, **kwargs):
        doc = DummyDoc(*args, **kwargs)
        routes = custom_routes if custom_routes else self.routes
        routes.add_doc(doc)
        return doc

    def setUp(self):
        self.routes = grow_routes.Routes()

    def test_routes_add(self):
        """Tests that routes can be added."""

        doc = self._add_doc(path='/', pod_path='/content/pages/home')
        _, pod_path, _ = self.routes.match('/')
        self.assertEquals(doc.pod_path, pod_path)
        doc_foo_bar = self._add_doc(
            path='/foo/bar', pod_path='/content/pages/foo')
        _, pod_path, _ = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar.pod_path, pod_path)

    def test_routes_add_operation(self):
        """Tests that routes can be added together."""

        doc = self._add_doc(path='/', pod_path='/content/pages/home')
        _, pod_path, _ = self.routes.match('/')
        self.assertEquals(doc.pod_path, pod_path)
        doc_foo_bar = self._add_doc(
            path='/foo/bar', pod_path='/content/pages/foo')
        _, pod_path, _ = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar.pod_path, pod_path)

        new_routes = grow_routes.Routes()
        doc_bar = self._add_doc(
            path='/bar', pod_path='/content/pages/bar', custom_routes=new_routes)
        _, pod_path, _ = new_routes.match('/bar')
        self.assertEquals(doc_bar.pod_path, pod_path)

        added_routes = self.routes + new_routes

        # Verify that the new routes has both the other route paths.
        _, pod_path, _ = added_routes.match('/')
        self.assertEquals(doc.pod_path, pod_path)
        _, pod_path, _ = added_routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar.pod_path, pod_path)
        _, pod_path, _ = added_routes.match('/bar')
        self.assertEquals(doc_bar.pod_path, pod_path)

        # Verify that the originals were not changed.
        _, pod_path, _ = self.routes.match('/')
        self.assertEquals(doc.pod_path, pod_path)
        _, pod_path, _ = self.routes.match('/bar')
        self.assertEquals(None, pod_path)
        _, pod_path, _ = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar.pod_path, pod_path)
        _, pod_path, _ = new_routes.match('/bar')
        self.assertEquals(doc_bar.pod_path, pod_path)
        _, pod_path, _ = new_routes.match('/foo/bar')
        self.assertEquals(None, pod_path)

    def test_routes_update_operation(self):
        """Tests that routes can be updated."""

        doc = self._add_doc(path='/', pod_path='/content/pages/home')
        _, pod_path, _ = self.routes.match('/')
        self.assertEquals(doc.pod_path, pod_path)
        doc_foo_bar = self._add_doc(
            path='/foo/bar', pod_path='/content/pages/foo/bar')
        _, pod_path, _ = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar.pod_path, pod_path)

        new_routes = grow_routes.Routes()
        doc_bar = self._add_doc(
            path='/bar', pod_path='/content/pages/bar', custom_routes=new_routes)
        _, pod_path, _ = new_routes.match('/bar')
        self.assertEquals(doc_bar.pod_path, pod_path)

        self.routes.update(new_routes)

        # Verify that the original routes has both the route paths.
        _, pod_path, _ = self.routes.match('/')
        self.assertEquals(doc.pod_path, pod_path)
        _, pod_path, _ = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar.pod_path, pod_path)
        _, pod_path, _ = self.routes.match('/bar')
        self.assertEquals(doc_bar.pod_path, pod_path)

        # Verify that the new routes were not changed.
        _, pod_path, _ = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar.pod_path, pod_path)
        _, pod_path, _ = new_routes.match('/bar')
        self.assertEquals(doc_bar.pod_path, pod_path)
        _, pod_path, _ = new_routes.match('/foo/bar')
        self.assertEquals(None, pod_path)

    def test_docs(self):
        """Tests that routes' docs can be retrieved."""

        # Add docs in random order.
        self._add_doc(path='/foo')
        self._add_doc(path='/bax/coo/lib')
        self._add_doc(path='/bax/bar')
        self._add_doc(path='/bax/pan')
        self._add_doc(path='/bax/coo/vin')
        self._add_doc(path='/tem/pon')

        # Expect the yielded docs to be in order.
        expected = [
            '/bax/bar', '/bax/coo/lib', '/bax/coo/vin', '/bax/pan',
            '/foo', '/tem/pon',
        ]
        actual = [path for path, _, _ in self.routes.docs]
        self.assertEquals(expected, actual)

    def test_remove(self):
        """Tests that paths can be removed."""

        doc = self._add_doc(path='/foo', pod_path='/content/foo')
        _, pod_path, _ = self.routes.match('/foo')
        self.assertEquals(doc.pod_path, pod_path)
        _, pod_path, _ = self.routes.remove('/foo')
        self.assertEquals(doc.pod_path, pod_path)
        _, pod_path, _ = self.routes.match('/foo')
        self.assertEquals(None, pod_path)



if __name__ == '__main__':
    unittest.main()
