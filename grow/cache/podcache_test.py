"""Test the pod caching container."""

from . import podcache
from grow import storage
from grow.pods import pods
from grow.testing import testing
import unittest

class PodCacheTestCase(unittest.TestCase):
    """Tests the PodCache object."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.cache = podcache.PodCache({}, {}, {}, None)
        self.cache._pod = self.pod

    def test_global_object_cache(self):
        """Using a global object cache."""
        self.cache.object_cache.add('question', '???')
        self.assertEqual({
            'question': '???',
        }, self.cache.object_cache.export())

    def test_has_object_cache(self):
        """Check if an object cache already exists."""
        self.assertEqual(False, self.cache.has_object_cache('named'))
        self.cache.get_object_cache('named')
        self.assertEqual(True, self.cache.has_object_cache('named'))

    def test_init(self):
        """Ability to initialize with an existing yaml file."""
        dep_cache = {
            '/content/test': [
                '/content/test1',
                '/content/test2',
            ]
        }
        obj_cache = {
            'named': {
                'values': {
                    'answer': 42,
                }
            }
        }
        routes_cache = {
            'version': 1,
            'concrete': {
                None: {
                    '/': {
                        'value': {
                            'kind': 'test',
                            'pod_path': 'pod_path',
                            'hashed': 'hashed',
                            'meta': {},
                        },
                        'options': {
                            'question': '30+12',
                        },
                    }
                }
            }
        }
        cache = podcache.PodCache(
            dep_cache=dep_cache, obj_cache=obj_cache, routes_cache=routes_cache,
            pod=None)

        self.assertEqual(
            {
                '/content/test': ['/content/test1', '/content/test2'],
            },
            cache.dependency_graph.export())

        self.assertEqual(
            {
                'answer': 42,
            },
            cache.get_object_cache('named').export())

        self.assertEqual(
            {
                'question': '30+12',
            },
            cache.routes_cache.get('/', concrete=True)['options'])

    def test_reset_object_cache_false(self):
        """Check if an object cache will reset."""
        named_cache = self.cache.create_object_cache(
            'named', can_reset=False)
        named_cache.add('question', '???')
        self.assertEqual({
            'question': '???',
        }, named_cache.export())
        self.cache.reset()
        self.assertEqual({
            'question': '???',
        }, named_cache.export())

    def test_reset_object_cache_true(self):
        """Check if an object cache will reset."""
        named_cache = self.cache.create_object_cache(
            'named', can_reset=True)
        named_cache.add('question', '???')
        self.assertEqual({
            'question': '???',
        }, named_cache.export())
        self.cache.reset()
        self.assertEqual({}, named_cache.export())

    def test_write_object_cache(self):
        """Naive test for writing an object cache file."""
        self.cache.object_cache.add('foo', 'bar')
        self.cache.write()

if __name__ == '__main__':
    unittest.main()
