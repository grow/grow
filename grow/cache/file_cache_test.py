"""Tests for the file cache."""

import unittest
from . import file_cache


class FileCacheTestCase(unittest.TestCase):
    """Tests for the file cache."""

    def setUp(self):
        self.test_cache = file_cache.FileCache()

    def test_add(self):
        """Test that adding to the file cache works."""
        self.test_cache.add('/content/answer.txt', {
            'answer': 42,
        })
        self.assertEqual(42, self.test_cache.get('/content/answer.txt')['answer'])

    def test_export(self):
        """Test that exporting the file cache works."""
        self.test_cache.add('/content/answer.txt', {
            'answer': 42,
        })
        self.test_cache.add('/content/question.txt', {
            'question': '???',
        })
        self.assertDictEqual({
            '/content/question.txt': {
                None: {
                    'question': '???',
                },
            },
            '/content/answer.txt': {
                None: {
                    'answer': 42,
                },
            },
        }, self.test_cache.export())

    def test_remove(self):
        """Test that paths can be removed from the cache."""
        self.test_cache.add('/content/answer.txt', {
            'answer': 42,
        })
        self.assertEqual(42, self.test_cache.get('/content/answer.txt')['answer'])
        self.assertEqual({
            None: {
                'answer': 42,
            },
        }, self.test_cache.remove('/content/answer.txt'))
        self.assertEqual(None, self.test_cache.get('/content/answer.txt'))


if __name__ == '__main__':
    unittest.main()
