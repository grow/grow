"""Test the storage"""

import unittest
from grow.storage import storage


class StoragerCase(unittest.TestCase):
    """Tests for the Timer"""

    def test_init(self):
        """Init with value correctly uses value."""
        storager = storage.Storager(storage='test')
        self.assertEqual('test', storager.storage)

    def test_init_default(self):
        """Init with no value."""
        storager = storage.Storager()
        self.assertEqual(storager.storage, None)


if __name__ == '__main__':
    unittest.main()
