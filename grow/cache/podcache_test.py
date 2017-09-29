"""Test the pod caching container."""

import unittest
from . import podcache


class PodCacheTestCase(unittest.TestCase):
    """Tests the PodCache object."""

    def setUp(self):
        self.cache = podcache.PodCache({}, {}, None)

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
        cache = podcache.PodCache(
            dep_cache=dep_cache, obj_cache=obj_cache, pod=None)

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

if __name__ == '__main__':
    unittest.main()
