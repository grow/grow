"""Tests for the routes cache."""

import unittest
from grow.cache import routes_cache


class RoutesCacheTestCase(unittest.TestCase):
    """Tests for the routes cache."""

    def setUp(self):
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
        })
        self.routes_cache.add('answer', {
            'question': '???'
        })
        self.assertDictEqual({
            routes_cache.EXPORT_KEY: {
                None: {
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
            'version': 1,
        }, self.routes_cache.export())

    def test_from_data(self):
        """Import from raw data."""
        def _generator(value):
            return value

        import_data = {
            routes_cache.EXPORT_KEY: {
                None: {
                    'answer': {
                        'options': None,
                        'value': 42,
                    },
                },
            },
            'version': 0,
        }

        # Old versions ar ignored.
        self.routes_cache.from_data(import_data, _generator)
        self.assertDictEqual({
            routes_cache.EXPORT_KEY: {},
            'version': routes_cache.VERSION,
        }, self.routes_cache.export())

        # Current version import data works.
        import_data['version'] = routes_cache.VERSION
        self.routes_cache.from_data(import_data, _generator)
        self.assertDictEqual(import_data, self.routes_cache.export())

    def test_mark_clean(self):
        """Can mark as clean?"""
        self.assertFalse(self.routes_cache.is_dirty)
        self.routes_cache.add('answer', 42)
        self.assertTrue(self.routes_cache.is_dirty)
        self.routes_cache.mark_clean()
        self.assertFalse(self.routes_cache.is_dirty)

    def test_remove(self):
        """Removing a key from the cache."""
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

    def test_reset(self):
        """Reset a key from the cache."""
        value = 42
        self.routes_cache.add('question', value)
        self.assertEqual(42, self.routes_cache.get('question')['value'])
        self.routes_cache.reset()
        self.assertEqual(None, self.routes_cache.get('question'))


if __name__ == '__main__':
    unittest.main()
