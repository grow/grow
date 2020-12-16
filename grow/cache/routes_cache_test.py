"""Tests for the routes cache."""

import unittest
from grow.pods import pods
from grow import storage
from grow.cache import routes_cache
from grow.testing import testing


class RoutesCacheTestCase(unittest.TestCase):
    """Tests for the routes cache."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.routes_cache = routes_cache.RoutesCache()

    def test_add(self):
        """Adding a value to the cache."""
        self.assertFalse(self.routes_cache.is_dirty)
        self.routes_cache.add('answer', 42)
        self.assertEqual(42, self.routes_cache.get('answer')['value'])
        self.assertTrue(self.routes_cache.is_dirty)

    def test_add_clean(self):
        """Adding a value to the cache with the same value does not make dirty."""
        self.assertFalse(self.routes_cache.is_dirty)
        self.routes_cache.add('answer', 42)
        self.assertEqual(42, self.routes_cache.get('answer')['value'])
        self.assertTrue(self.routes_cache.is_dirty)
        self.routes_cache.mark_clean()
        self.assertFalse(self.routes_cache.is_dirty)
        self.routes_cache.add('answer', 42)
        self.assertFalse(self.routes_cache.is_dirty)

    def test_add_dirty(self):
        """Adding a value to the cache with the different value makes dirty."""
        self.assertFalse(self.routes_cache.is_dirty)
        self.routes_cache.add('answer', 42)
        self.assertEqual(42, self.routes_cache.get('answer')['value'])
        self.assertTrue(self.routes_cache.is_dirty)
        self.routes_cache.mark_clean()
        self.assertFalse(self.routes_cache.is_dirty)
        self.routes_cache.add('answer', 2)
        self.assertTrue(self.routes_cache.is_dirty)

    def test_export(self):
        """Raw cache export."""
        self.routes_cache.add('question', {
            'answer': 42
        }, concrete=False)
        self.routes_cache.add('answer', {
            'question': '???'
        }, concrete=False)
        self.routes_cache.add('query', {
            'query': 'What is blue?'
        }, concrete=True, options={'dev': True})
        self.assertDictEqual({
            'dynamic': {
                '__None__': {
                    'answer': {
                        'options': None,
                        'value': {
                            'question': '???'
                        },
                    },
                    'question': {
                        'options': None,
                        'value': {
                            'answer': 42
                        },
                    },
                },
            },
            'concrete': {
                '__None__': {
                    'query': {
                        'options': {
                            'dev': True,
                        },
                        'value': {
                            'query': 'What is blue?',
                        },
                    },
                },
            },
            'version': 1,
        }, self.routes_cache.export())

    def test_mark_clean(self):
        """Can mark as clean?"""
        self.assertFalse(self.routes_cache.is_dirty)
        self.routes_cache.add('answer', 42)
        self.assertTrue(self.routes_cache.is_dirty)
        self.routes_cache.mark_clean()
        self.assertFalse(self.routes_cache.is_dirty)

    def test_remove(self):
        """Test removing a key from the cache."""
        value = {
            'answer': 42
        }
        self.routes_cache.add('question', value)
        self.assertEqual(42, self.routes_cache.get('question')['value']['answer'])
        self.routes_cache.mark_clean()
        self.assertFalse(self.routes_cache.is_dirty)
        self.assertEqual(
            {
                'options': None,
                'value': value,
            }, self.routes_cache.remove('question'))
        self.assertEqual(None, self.routes_cache.get('question'))
        self.assertTrue(self.routes_cache.is_dirty)


if __name__ == '__main__':
    unittest.main()
