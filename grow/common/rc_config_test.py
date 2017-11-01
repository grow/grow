"""Tests for RC Config."""

import unittest
from grow.common import rc_config


def mock_time(value):
    """Mock out the time value."""
    def _mock():
        return value
    return _mock


class RCConfigTestCase(unittest.TestCase):
    """Test the RC Config."""

    def _create_config(self, time_value=None):
        self.config = rc_config.RCConfig(config={}, internal_time=mock_time(time_value))

    def setUp(self):
        self._create_config()

    def test_last_checked(self):
        """Test the last_checked."""
        self.assertEqual(0, self.config.last_checked)
        self.config.set('update.last_checked', 12345)
        self.assertEqual(12345, self.config.last_checked)

    def test_set(self):
        """Test that set works on the config."""
        self.config.set('update.last_checked', 12345)
        self.assertEqual(12345, self.config.get('update.last_checked'))
