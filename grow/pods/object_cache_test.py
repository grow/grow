"""Tests for the object cache."""

import re
import unittest
from grow.testing import testing
from . import object_cache
from . import pods
from . import storage


class ObjectCacheTestCase(unittest.TestCase):
    """Tests for the object cache."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.obj_cache = object_cache.ObjectCache()

    def test_add(self):
        """Adding a value to the cache."""
        self.obj_cache.add('answer', 42)
        self.assertEqual(42, self.obj_cache.get('answer'))

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
        self.assertEqual(False, 'answer' in self.obj_cache)
        self.obj_cache.add('answer', 42)
        self.assertEqual(True, 'answer' in self.obj_cache)

    def test_remove(self):
        """Test removing a key from the cache."""
        value = {
            'answer': 42
        }
        self.obj_cache.add('question', value)
        self.assertEqual(42, self.obj_cache.get('question')['answer'])
        self.assertEqual(value, self.obj_cache.remove('question'))
        self.assertEqual(None, self.obj_cache.get('question'))

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
