"""Tests for Base Config."""

import unittest
from grow.common import base_config


class BaseConfigTestCase(unittest.TestCase):
    """Test the RC Config."""

    def setUp(self):
        self.config = base_config.BaseConfig(config={})

    def test_get_empty(self):
        """Test that get works on the config with default."""
        self.config = base_config.BaseConfig(config=None)
        self.assertEqual(42, self.config.get('foo', 42))
        self.assertEqual(42, self.config.get('foo.bar', 42))

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


class BaseConfigPrefixedTestCase(unittest.TestCase):
    """Test the RC Config Prefixed utility."""

    def setUp(self):
        self.config = base_config.BaseConfig(config={})
        self.prefixed = self.config.prefixed('base')

    def test_prefix(self):
        """Prefixed manipulation should work."""
        # Using the config to set.
        self.assertEqual(None, self.prefixed.get('foo'))
        self.config.set('base.foo', 'bar')
        self.assertEqual('bar', self.prefixed.get('foo'))

        # Using the prefixed set.
        self.prefixed.set('bar', 'faz')
        self.assertEqual('faz', self.config.get('base.bar'))
        self.assertEqual('faz', self.prefixed.get('bar'))

    def test_normailize_prefix(self):
        """Normalized prefixes."""
        normalize = base_config.BaseConfigPrefixed.normalize_prefix
        self.assertEqual('pod.', normalize('pod'))
        self.assertEqual('', normalize(''))
        self.assertEqual('nested.path.', normalize('nested.path'))
        self.assertEqual('path.', normalize('   path   '))
