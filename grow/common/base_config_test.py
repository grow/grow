"""Tests for Base Config."""

import unittest
from grow.common import base_config


class BaseConfigTestCase(unittest.TestCase):
    """Test the RC Config."""

    def setUp(self):
        self.config = base_config.BaseConfig(config={})

    def test_get_default(self):
        """Test that get works on the config with default."""
        self.assertEqual(42, self.config.get('foo', 42))

        self.config.set('update.last_checked', 12345)
        self.assertEqual(12, self.config.get('update.foo', 12))

    def test_set_root(self):
        """Test that set works on the config with root keys."""
        self.assertEqual(None, self.config.get('foo'))
        self.config.set('foo', 'bar')
        self.assertEqual('bar', self.config.get('foo'))

    def test_set_nested(self):
        """Test that set works on the config with sub keys."""
        self.assertEqual(None, self.config.get('update.last_checked'))
        self.config.set('update.last_checked', 12345)
        self.assertEqual(12345, self.config.get('update.last_checked'))
        expected = {
            'update': {
                'last_checked': 12345,
            },
        }
        self.assertEqual(expected, self.config.export())
