"""Tests for the object cache."""

import re
import unittest
from grow.pods import pods
from grow import storage
from grow.testing import testing
from . import object_cache


class ObjectCacheTestCase(unittest.TestCase):
    """Tests for the object cache."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.obj_cache = object_cache.ObjectCache()

    def test_add(self):
        """Adding a value to the cache."""
        self.assertFalse(self.obj_cache.is_dirty)
        self.obj_cache.add('answer', 42)
        self.assertEqual(42, self.obj_cache.get('answer'))
        self.assertTrue(self.obj_cache.is_dirty)

    def test_add_clean(self):
        """Adding a value to the cache with the same value does not make dirty."""
        self.assertFalse(self.obj_cache.is_dirty)
        self.obj_cache.add('answer', 42)
        self.assertEqual(42, self.obj_cache.get('answer'))
        self.assertTrue(self.obj_cache.is_dirty)
        self.obj_cache.mark_clean()
        self.assertFalse(self.obj_cache.is_dirty)
        self.obj_cache.add('answer', 42)
        self.assertFalse(self.obj_cache.is_dirty)

    def test_add_dirty(self):
        """Adding a value to the cache with the different value makes dirty."""
        self.assertFalse(self.obj_cache.is_dirty)
        self.obj_cache.add('answer', 42)
        self.assertEqual(42, self.obj_cache.get('answer'))
        self.assertTrue(self.obj_cache.is_dirty)
        self.obj_cache.mark_clean()
        self.assertFalse(self.obj_cache.is_dirty)
        self.obj_cache.add('answer', 2)
        self.assertTrue(self.obj_cache.is_dirty)

    def test_add_all(self):
        """Overwrite with a dictionary of cached values."""
        self.obj_cache.add_all({
            '/content/pages/intro.md': {
                'question': '???'
            }
        })
        self.assertEqual('???', self.obj_cache.get(
            '/content/pages/intro.md')['question'])

    def test_export(self):
        """Raw cache export."""
        self.obj_cache.add('question', {
            'answer': 42
        })
        self.obj_cache.add('answer', {
            'question': '???'
        })
        self.assertDictEqual({
            'answer': {
                'question': '???'
            },
            'question': {
                'answer': 42
            },
        }, self.obj_cache.export())

    def test_contains(self):
        """Contains a value to the cache?"""
        self.assertFalse('answer' in self.obj_cache)
        self.obj_cache.add('answer', 42)
        self.assertTrue('answer' in self.obj_cache)

    def test_mark_clean(self):
        """Can mark as clean?"""
        self.assertFalse(self.obj_cache.is_dirty)
        self.obj_cache.add('answer', 42)
        self.assertTrue(self.obj_cache.is_dirty)
        self.obj_cache.mark_clean()
        self.assertFalse(self.obj_cache.is_dirty)

    def test_remove(self):
        """Test removing a key from the cache."""
        value = {
            'answer': 42
        }
        self.obj_cache.add('question', value)
        self.assertEqual(42, self.obj_cache.get('question')['answer'])
        self.obj_cache.mark_clean()
        self.assertFalse(self.obj_cache.is_dirty)
        self.assertEqual(value, self.obj_cache.remove('question'))
        self.assertEqual(None, self.obj_cache.get('question'))
        self.assertTrue(self.obj_cache.is_dirty)

    def test_search(self):
        """Test searching for matching keys from the cache."""

        self.obj_cache.add('answer', 42)
        self.obj_cache.add('motivation', 'holy hand grenade')
        self.obj_cache.add('question', '???')
        self.obj_cache.add('quest', 'to follow that star')

        self.assertEqual({'answer': 42}, self.obj_cache.search(r'^ans*'))
        self.assertEqual({
            'motivation': 'holy hand grenade',
            'question': '???',
        }, self.obj_cache.search(re.compile(r'ion$')))
        self.assertEqual({
            'quest': 'to follow that star',
            'question': '???',
        }, self.obj_cache.search(r'^quest'))


if __name__ == '__main__':
    unittest.main()
