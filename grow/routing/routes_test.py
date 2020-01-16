"""Tests for the routes."""

import unittest
from grow.routing import routes as grow_routes


class RoutesTestCase(unittest.TestCase):
    """Test the routes."""

    def _add(self, path, value=None, options=None, custom_routes=None):
        routes = custom_routes if custom_routes is not None else self.routes
        routes.add(path, value, options=options)
        return {
            'path': path,
            'value': value,
            'options': options,
        }

    def setUp(self):
        self.routes = grow_routes.Routes()

    def test_routes_add(self):
        """Tests that routes can be added."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo')
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)

    def test_routes_add_params_values(self):
        """Tests that routes can be added with values for params."""
        options = {
            'locale': [
                'en',
                'es'
            ]
        }
        doc = self._add('/:locale/', '/content/pages/home', options=options)
        result = self.routes.match('/en/')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/es/')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/fr/')
        self.assertEqual(None, result)

        # Adding another option adds to the set of locale options.
        options = {
            'locale': [
                'fr',
            ]
        }
        doc_new = self._add('/:locale/about', '/content/pages/about', options=options)
        result = self.routes.match('/es/about')
        self.assertEqual(doc_new['value'], result.value)
        result = self.routes.match('/fr/about')
        self.assertEqual(doc_new['value'], result.value)
        result = self.routes.match('/de/about')
        self.assertEqual(None, result)

    def test_routes_add_params_inline_values(self):
        """Tests that routes can be added with values for mid-string params."""
        options = {
            'locale': [
                'en',
                'es'
            ]
        }
        doc = self._add('/index-{locale}.html', '/content/pages/home', options=options)
        result = self.routes.match('/index-en.html')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/index-es.html')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/index-fr.html')
        self.assertEqual(None, result)

        # Cannot have multiple adds for min-string params.
        with self.assertRaises(grow_routes.PathConflictError):
            self._add('/index-{locale}.html', '/content/pages/bar')

    def test_routes_add_params_inline_values_multi(self):
        """Tests that routes can be added with values for mid-string multiple params."""
        options = {
            'env': [
                'prod',
                'staging'
            ],
            'locale': [
                'en',
                'es'
            ],
        }
        doc = self._add('/index-{locale}-{env}.html', '/content/pages/home', options=options)
        result = self.routes.match('/index-en-prod.html')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/index-es-prod.html')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/index-fr-prod.html')
        self.assertEqual(None, result)
        result = self.routes.match('/index-en-staging.html')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/index-es-staging.html')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/index-fr-staging.html')
        self.assertEqual(None, result)

        # Cannot have multiple adds for min-string params.
        with self.assertRaises(grow_routes.PathConflictError):
            self._add('/index-{locale}-{env}.html', '/content/pages/bar')

    def test_routes_add_params_inline_values_missing(self):
        """Tests that routes can be added with values for mid-string missing params."""
        options = {
            'locale': [
                'en',
                'es'
            ],
        }

        # Cannot use with template without options.
        with self.assertRaises(grow_routes.MissingOptionError):
            self._add('/index-{locale}-{env}.html', '/content/pages/home', options=options)

    def test_routes_add_conflict(self):
        """Tests that routes can be added but not conflicting."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        with self.assertRaises(grow_routes.PathConflictError):
            self._add('/', '/content/pages/bar')

    def test_routes_add_conflict_param(self):
        """Tests that routes can be added but not conflicting."""

        doc = self._add('/:foo', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        with self.assertRaises(grow_routes.PathConflictError):
            self._add('/:foo', '/content/pages/bar')

    def test_routes_add_conflict_param_name(self):
        """Tests that routes can be added but not conflicting."""

        doc = self._add('/:foo', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        with self.assertRaises(grow_routes.PathParamNameConflictError):
            self._add('/:bar', '/content/pages/bar')

    def test_routes_add_conflict_wildcard(self):
        """Tests that routes can be added but not conflicting."""

        doc = self._add('/*', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        with self.assertRaises(grow_routes.PathConflictError):
            self._add('/*', '/content/pages/bar')

    def test_routes_add_operation(self):
        """Tests that routes can be added together."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo')
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)

        new_routes = grow_routes.Routes()
        doc_bar = self._add('/bar', '/content/pages/bar',
                            custom_routes=new_routes)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        added_routes = self.routes + new_routes

        # Verify that the new routes has both the other route paths.
        result = added_routes.match('/')
        self.assertEqual(doc['value'], result.value)
        result = added_routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = added_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        # Verify that the originals were not changed.
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/bar')
        self.assertEqual(None, result)
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)
        result = new_routes.match('/foo/bar')
        self.assertEqual(None, result)

    def test_routes_update_operation(self):
        """Tests that routes can be updated."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo/bar')
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)

        new_routes = grow_routes.Routes()
        doc_bar = self._add(
            '/bar', '/content/pages/bar', custom_routes=new_routes)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        self.routes.update(new_routes)

        # Verify that the original routes has both the route paths.
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = self.routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        # Verify that the new routes were not changed.
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)
        result = new_routes.match('/foo/bar')
        self.assertEqual(None, result)

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
        actual = [path for path, _, _ in self.routes.nodes]
        self.assertEqual(expected, actual)

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
        self.assertEqual(expected, actual)

    def test_filter(self):
        """Tests that routes' can be filtered."""

        # Add nodes in random order.
        self._add('/foo', value=1)
        self._add('/bax/coo/lib', value=2)
        self._add('/bax/bar', value=3)
        self._add('/bax/pan', value=4)
        self._add('/bax/:coo/vin', value=5)
        self._add('/tem/pon', value=6)

        # Expect the yielded nodes to be in order.
        expected = [
            '/bax/bar', '/bax/coo/lib', '/bax/pan', '/bax/:coo/vin',
            '/foo', '/tem/pon',
        ]
        actual = list(self.routes.paths)
        self.assertEqual(expected, actual)
        self.routes.filter(None)  # Does nothing.
        self.assertEqual(expected, actual)

        # Filter specific nodes and test new paths.
        def _filter_func(_, value):
            if value in (2, 5):
                return False
            return True

        self.routes.filter(_filter_func)

        expected = ['/bax/bar', '/bax/pan', '/foo', '/tem/pon']
        actual = list(self.routes.paths)
        self.assertEqual(expected, actual)

    def test_remove(self):
        """Tests that paths can be removed."""

        doc = self._add('/foo', '/content/foo')
        result = self.routes.match('/foo')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.remove('/foo')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/foo')
        self.assertEqual(None, result)

    def test_remove_param(self):
        """Tests that param paths can be removed."""

        doc = self._add('/:foo', '/content/foo')
        result = self.routes.match('/foo')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.remove('/:foo')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/foo')
        self.assertEqual(None, result)

    def test_remove_wildcard(self):
        """Tests that wildcard paths can be removed."""

        doc = self._add('/*foo', '/content/foo')
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.remove('/*foo')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/foo/bar')
        self.assertEqual(None, result)

    def test_param(self):
        """Test that params work for matching paths."""

        # Top level param.
        doc = self._add('/path/:bar', '/static')
        result = self.routes.match('/path/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'bar': 'foo'
        })
        result = self.routes.match('/path/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'bar': 'bar'
        })

        # Nested param.
        doc = self._add('/path/to/:bar', '/static')
        result = self.routes.match('/path/to/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'bar': 'foo'
        })
        result = self.routes.match('/path/to/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'bar': 'bar'
        })

        # Root param.
        doc = self._add('/path/of/:baz', '/static')
        result = self.routes.match('/path/of/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'foo'
        })
        result = self.routes.match('/path/of/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'bar'
        })

        # Middle param.
        doc = self._add('/of/:baz/to', '/static')
        result = self.routes.match('/of/foo/to')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'foo'
        })
        result = self.routes.match('/of/baz/to')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'baz'
        })

    def test_param_multi(self):
        """Test that multiple params work for matching paths."""

        doc = self._add('/path/:bar/:baz', '/static')
        result = self.routes.match('/path/foo/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'bar': 'foo',
            'baz': 'bar',
        })
        result = self.routes.match('/path/bar/baz')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'bar': 'bar',
            'baz': 'baz',
        })

    def test_wildcard(self):
        """Test that wildcards work for matching paths."""

        # Top level wildcard.
        doc = self._add('/path/*', '/static')
        result = self.routes.match('/path/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            '*': 'foo'
        })
        result = self.routes.match('/path/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            '*': 'bar'
        })

        # Nested wildcard.
        doc = self._add('/path/to/*', '/static')
        result = self.routes.match('/path/to/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            '*': 'foo'
        })
        result = self.routes.match('/path/to/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            '*': 'bar'
        })

        # Root wildcard.
        doc = self._add('/*', '/static')
        result = self.routes.match('/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            '*': 'foo'
        })
        result = self.routes.match('/foo/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            '*': 'foo/bar'
        })

    def test_wildcard_named(self):
        """Test that named wildcards work for matching paths."""

        # Top level wildcard.
        doc = self._add('/path/*baz', '/static')
        result = self.routes.match('/path/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'foo'
        })
        result = self.routes.match('/path/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'bar'
        })

        # Nested wildcard.
        doc = self._add('/path/to/*baz', '/static')
        result = self.routes.match('/path/to/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'foo'
        })
        result = self.routes.match('/path/to/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'bar'
        })

        # Root wildcard.
        doc = self._add('/*baz', '/static')
        result = self.routes.match('//foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'foo'
        })
        result = self.routes.match('/foo/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'baz': 'foo/bar'
        })

    def test_wildcard_params(self):
        """Test that wildcards and params work together for matching paths."""

        # Mixing a param with a wildcard.
        doc = self._add('/:path/*', '/static')
        result = self.routes.match('/path/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'path',
            '*': 'foo',
        })
        result = self.routes.match('/foo/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'foo',
            '*': 'bar',
        })

        # Mixing a param with a wildcard in a nested path.
        doc = self._add('/root/:path/*', '/static')
        result = self.routes.match('/root/path/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'path',
            '*': 'foo',
        })
        result = self.routes.match('/root/foo/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'foo',
            '*': 'bar',
        })

    def test_wildcard_named_params(self):
        """Test that named wildcards and params work for matching paths."""

        # Mixing a param with a wildcard.
        doc = self._add('/:path/*baz', '/static')
        result = self.routes.match('/path/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'path',
            'baz': 'foo',
        })
        result = self.routes.match('/foo/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'foo',
            'baz': 'bar',
        })

        # Mixing a param with a wildcard in a nested path.
        doc = self._add('/root/:path/*baz', '/static')
        result = self.routes.match('/root/path/foo')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'path',
            'baz': 'foo',
        })
        result = self.routes.match('/root/foo/bar')
        self.assertEqual(result.path, doc['path'])
        self.assertEqual(result.value, doc['value'])
        self.assertEqual(result.params, {
            'path': 'foo',
            'baz': 'bar',
        })


class RoutesSimpleTestCase(unittest.TestCase):
    """Test the routes."""

    def _add(self, path, value=None, custom_routes=None):
        routes = custom_routes if custom_routes is not None else self.routes
        routes.add(path, value)
        return {
            'path': path,
            'value': value,
        }

    def setUp(self):
        self.routes = grow_routes.RoutesSimple()

    def test_routes_add(self):
        """Tests that routes can be added."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo')
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)

    def test_routes_add_conflict(self):
        """Tests that routes can be added but not conflicting."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        with self.assertRaises(grow_routes.PathConflictError):
            self._add('/', '/content/pages/bar')

    def test_routes_add_operation(self):
        """Tests that routes can be added together."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo')
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)

        new_routes = grow_routes.RoutesSimple()
        doc_bar = self._add('/bar', '/content/pages/bar',
                            custom_routes=new_routes)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        added_routes = self.routes + new_routes

        # Verify that the new routes has both the other route paths.
        result = added_routes.match('/')
        self.assertEqual(doc['value'], result.value)
        result = added_routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = added_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        # Verify that the originals were not changed.
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/bar')
        self.assertEqual(None, result)
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)
        result = new_routes.match('/foo/bar')
        self.assertEqual(None, result)

    def test_routes_update_operation(self):
        """Tests that routes can be updated."""

        doc = self._add('/', '/content/pages/home')
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        doc_foo_bar = self._add('/foo/bar', '/content/pages/foo/bar')
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)

        new_routes = grow_routes.RoutesSimple()
        doc_bar = self._add(
            '/bar', '/content/pages/bar', custom_routes=new_routes)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        self.routes.update(new_routes)

        # Verify that the original routes has both the route paths.
        result = self.routes.match('/')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = self.routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)

        # Verify that the new routes were not changed.
        result = self.routes.match('/foo/bar')
        self.assertEqual(doc_foo_bar['value'], result.value)
        result = new_routes.match('/bar')
        self.assertEqual(doc_bar['value'], result.value)
        result = new_routes.match('/foo/bar')
        self.assertEqual(None, result)

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
        actual = [path for path, _, _ in self.routes.nodes]
        self.assertEqual(expected, actual)

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
        self.assertEqual(expected, actual)

    def test_filter(self):
        """Tests that routes' can be filtered."""

        # Add nodes in random order.
        self._add('/foo', value=1)
        self._add('/bax/coo/lib', value=2)
        self._add('/bax/bar', value=3)
        self._add('/bax/pan', value=4)
        self._add('/bax/coo/vin', value=5)
        self._add('/tem/pon', value=6)

        # Expect the yielded nodes to be in order.
        expected = [
            '/bax/bar', '/bax/coo/lib', '/bax/coo/vin', '/bax/pan',
            '/foo', '/tem/pon',
        ]
        actual = list(self.routes.paths)
        self.assertEqual(expected, actual)

        # Filter specific nodes and test new paths.
        def _filter_func(_, value):
            if value in (2, 5):
                return False
            return True

        self.routes.filter(_filter_func)

        expected = ['/bax/bar', '/bax/pan', '/foo', '/tem/pon']
        actual = list(self.routes.paths)
        self.assertEqual(expected, actual)

    def test_shard(self):
        """Tests that routes' can be sharded equally."""

        def _reset_routes():
            self.routes = grow_routes.RoutesSimple()

            # Add nodes in random order.
            self._add('/foo', value=1)
            self._add('/bax/coo/lib', value=2)
            self._add('/bax/bar', value=3)
            self._add('/bax/pan', value=4)
            self._add('/bax/coo/vin', value=5)
            self._add('/tem/pon', value=6)

            # Expect the yielded nodes to be in order.
            expected = [
                '/bax/bar', '/bax/coo/lib', '/bax/coo/vin', '/bax/pan',
                '/foo', '/tem/pon',
            ]
            actual = list(self.routes.paths)
            self.assertEqual(expected, actual)

        # Shard 1
        _reset_routes()
        self.routes.shard(3, 1, attr=None)
        expected = sorted([
            '/bax/bar', '/bax/pan',
        ])
        actual = sorted(list(self.routes.paths))
        self.assertEqual(expected, actual)

        # Shard 2
        _reset_routes()
        self.routes.shard(3, 2, attr=None)
        expected = sorted([
            '/bax/coo/lib', '/foo',
        ])
        actual = sorted(list(self.routes.paths))
        self.assertEqual(expected, actual)

        # Shard 3
        _reset_routes()
        self.routes.shard(3, 3, attr=None)

        expected = sorted([
            '/bax/coo/vin', '/tem/pon',
        ])
        actual = sorted(list(self.routes.paths))
        self.assertEqual(expected, actual)

    def test_shard_attr(self):
        """Tests that routes' can be sharded equally by attribute."""


        # pylint: disable=too-few-public-methods
        class _RouteInfo(object):
            """Organize information stored in the routes."""

            def __init__(self, kind):
                self.kind = kind


        def _reset_routes():
            self.routes = grow_routes.RoutesSimple()

            self._add('/bax/bar', value=_RouteInfo('doc'))  # 1 - doc
            self._add('/bax/coo/lib', value=_RouteInfo('static'))  # 1 - static
            self._add('/bax/coo/vin', value=_RouteInfo('static'))  # 2 - static
            self._add('/bax/pan', value=_RouteInfo('doc'))  # 2 - doc
            self._add('/bax/pan/taw', value=_RouteInfo('static'))  # 3 - static
            self._add('/bax/vew/vin', value=_RouteInfo('doc'))  # 3 - doc
            self._add('/fes/pon', value=_RouteInfo(None))  # 1 - default
            self._add('/foo', value=_RouteInfo('doc'))  # 1 - doc
            self._add('/tem/pon', value=_RouteInfo('static'))  # 1 - static
            self._add('/tem/tan', value=_RouteInfo('static'))  # 2 - static

            # Expect the yielded nodes to be in order.
            expected = sorted([
                '/bax/bar', '/bax/coo/lib', '/bax/coo/vin', '/bax/pan',
                '/foo', '/tem/pon', '/bax/pan/taw', '/bax/vew/vin', '/fes/pon',
                '/tem/tan',
            ])
            actual = sorted(list(self.routes.paths))
            self.assertEqual(expected, actual)

        # Shard 1
        _reset_routes()
        self.routes.shard(3, 1)
        expected = sorted(['/bax/bar', '/bax/coo/lib', '/fes/pon', '/foo', '/tem/pon'])
        actual = sorted(list(self.routes.paths))
        self.assertEqual(expected, actual)

        # Shard 2
        _reset_routes()
        self.routes.shard(3, 2)
        expected = sorted(['/bax/coo/vin', '/bax/pan', '/tem/tan'])
        actual = sorted(list(self.routes.paths))
        self.assertEqual(expected, actual)

        # Shard 3
        _reset_routes()
        self.routes.shard(3, 3)

        expected = sorted(['/bax/pan/taw', '/bax/vew/vin'])
        actual = sorted(list(self.routes.paths))
        self.assertEqual(expected, actual)

    def test_shard_errors(self):
        """Tests that errors happen with invalid shard values."""

        # Add nodes in random order.
        self._add('/foo', value=1)
        self._add('/bax/coo/lib', value=2)
        self._add('/bax/bar', value=3)
        self._add('/bax/pan', value=4)
        self._add('/bax/coo/vin', value=5)
        self._add('/tem/pon', value=6)

        with self.assertRaises(ValueError):
            self.routes.shard(0, 1)

        with self.assertRaises(ValueError):
            self.routes.shard(50, 1)

        with self.assertRaises(ValueError):
            self.routes.shard(1, 1)

        with self.assertRaises(ValueError):
            self.routes.shard(5, 6)

        with self.assertRaises(ValueError):
            self.routes.shard(5, 0)

    def test_remove(self):
        """Tests that paths can be removed."""

        doc = self._add('/foo', '/content/foo')
        result = self.routes.match('/foo')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.remove('/foo')
        self.assertEqual(doc['value'], result.value)
        result = self.routes.match('/foo')
        self.assertEqual(None, result)


if __name__ == '__main__':
    unittest.main()
