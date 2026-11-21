"""Tests for SimpleCache."""

import unittest

from grow.cache import simple_cache


class SimpleCacheTestCase(unittest.TestCase):
    """Tests for the in-memory SimpleCache."""

    def test_get_set_delete_clear(self):
        cache = simple_cache.SimpleCache(default_timeout=0)
        self.assertIsNone(cache.get('missing'))
        self.assertFalse(cache.has('missing'))

        self.assertTrue(cache.set('k', b'val'))
        self.assertTrue(cache.has('k'))
        self.assertEqual(b'val', cache.get('k'))
        self.assertFalse(cache.add('k', b'other'))
        self.assertEqual(b'val', cache.get('k'))

        self.assertTrue(cache.delete('k'))
        self.assertFalse(cache.delete('k'))
        self.assertIsNone(cache.get('k'))

        cache.set_many({'a': 1, 'b': 2})
        self.assertEqual([1, 2, None], cache.get_many('a', 'b', 'c'))
        cache.clear()
        self.assertIsNone(cache.get('a'))

    def test_pruning_threshold(self):
        cache = simple_cache.SimpleCache(threshold=2, default_timeout=0)
        cache.set('a', 1)
        cache.set('b', 2)
        cache.set('c', 3)
        cache.set('d', 4)
        self.assertLessEqual(len(cache._cache), 3)
