"""Tests for the routes."""

import unittest
from grow.routing import routes as grow_routes


class RoutesTestCase(unittest.TestCase):
    """Test the routes."""

    def _add(self, path, value=None, custom_routes=None):
        routes = custom_routes if custom_routes is not None else self.routes
        routes.add(path, value)
        return {
            'path': path,
            'value': value,
        }

    def setUp(self):
        self.routes = grow_routes.Routes()

    def test_routes_add(self):
        """Tests that routes can be added."""

        doc = self._add('/', '/content/pages/home')
        _, pod_path = self.routes.match('/')
        self.assertEquals(doc['value'], pod_path)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo')
        _, pod_path = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar['value'], pod_path)

    def test_routes_add_operation(self):
        """Tests that routes can be added together."""

        doc = self._add('/', '/content/pages/home')
        _, pod_path = self.routes.match('/')
        self.assertEquals(doc['value'], pod_path)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo')
        _, pod_path = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar['value'], pod_path)

        new_routes = grow_routes.Routes()
        doc_bar = self._add('/bar', '/content/pages/bar',
                            custom_routes=new_routes)
        _, pod_path = new_routes.match('/bar')
        print list(new_routes.nodes)
        self.assertEquals(doc_bar['value'], pod_path)

        added_routes = self.routes + new_routes

        # Verify that the new routes has both the other route paths.
        _, pod_path = added_routes.match('/')
        self.assertEquals(doc['value'], pod_path)
        _, pod_path = added_routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar['value'], pod_path)
        _, pod_path = added_routes.match('/bar')
        self.assertEquals(doc_bar['value'], pod_path)

        # Verify that the originals were not changed.
        _, pod_path = self.routes.match('/')
        self.assertEquals(doc['value'], pod_path)
        _, pod_path = self.routes.match('/bar')
        self.assertEquals(None, pod_path)
        _, pod_path = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar['value'], pod_path)
        _, pod_path = new_routes.match('/bar')
        self.assertEquals(doc_bar['value'], pod_path)
        _, pod_path = new_routes.match('/foo/bar')
        self.assertEquals(None, pod_path)

    def test_routes_update_operation(self):
        """Tests that routes can be updated."""

        doc = self._add('/', '/content/pages/home')
        _, pod_path = self.routes.match('/')
        self.assertEquals(doc['value'], pod_path)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo/bar')
        _, pod_path = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar['value'], pod_path)

        new_routes = grow_routes.Routes()
        doc_bar = self._add(
            '/bar', '/content/pages/bar', custom_routes=new_routes)
        _, pod_path = new_routes.match('/bar')
        self.assertEquals(doc_bar['value'], pod_path)

        self.routes.update(new_routes)

        # Verify that the original routes has both the route paths.
        _, pod_path = self.routes.match('/')
        self.assertEquals(doc['value'], pod_path)
        _, pod_path = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar['value'], pod_path)
        _, pod_path = self.routes.match('/bar')
        self.assertEquals(doc_bar['value'], pod_path)

        # Verify that the new routes were not changed.
        _, pod_path = self.routes.match('/foo/bar')
        self.assertEquals(doc_foo_bar['value'], pod_path)
        _, pod_path = new_routes.match('/bar')
        self.assertEquals(doc_bar['value'], pod_path)
        _, pod_path = new_routes.match('/foo/bar')
        self.assertEquals(None, pod_path)

    def test_nodes(self):
        """Tests that routes' nodes can be retrieved."""

        # Add nodes in random order.
        self._add('/foo')
        self._add('/bax/coo/lib')
        self._add('/bax/bar')
        self._add('/bax/pan')
        self._add('/bax/coo/vin')
        self._add('/tem/pon')

        # Expect the yielded nodes to be in order.
        expected = [
            '/bax/bar', '/bax/coo/lib', '/bax/coo/vin', '/bax/pan',
            '/foo', '/tem/pon',
        ]
        actual = [path for path, _ in self.routes.nodes]
        self.assertEquals(expected, actual)

    def test_paths(self):
        """Tests that routes' paths can be retrieved."""

        # Add nodes in random order.
        self._add('/foo')
        self._add('/bax/coo/lib')
        self._add('/bax/bar')
        self._add('/bax/pan')
        self._add('/bax/coo/vin')
        self._add('/tem/pon')

        # Expect the yielded nodes to be in order.
        expected = [
            '/bax/bar', '/bax/coo/lib', '/bax/coo/vin', '/bax/pan',
            '/foo', '/tem/pon',
        ]
        actual = list(self.routes.paths)
        self.assertEquals(expected, actual)

    def test_remove(self):
        """Tests that paths can be removed."""

        doc = self._add('/foo', '/content/foo')
        _, pod_path = self.routes.match('/foo')
        self.assertEquals(doc['value'], pod_path)
        _, pod_path = self.routes.remove('/foo')
        self.assertEquals(doc['value'], pod_path)
        _, pod_path = self.routes.match('/foo')
        self.assertEquals(None, pod_path)


if __name__ == '__main__':
    unittest.main()
