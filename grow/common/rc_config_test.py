"""Tests for RC Config."""

import os
import tempfile
import unittest
from grow.common import rc_config


def mock_time(value):
    """Mock out the time value."""
    def _mock():
        return value
    return _mock


class RCConfigTestCase(unittest.TestCase):
    """Test the RC Config."""

    def _create_config(self, config=None, time_value=None, filename=None,
                       wd_filename=None):
        self.config = rc_config.RCConfig(
            config=config, internal_time=mock_time(time_value), filename=filename,
            wd_filename=wd_filename)

    def setUp(self):
        self._create_config(config={})

    def test_last_checked(self):
        """Test the last_checked."""
        self.assertEqual(0, self.config.last_checked)
        self.config.set('update.last_checked', 12345)
        self.assertEqual(12345, self.config.last_checked)

    def test_last_checked_reset(self):
        """Test the last_checked reset works."""
        self._create_config(config={}, time_value=100)
        self.config.set('update.last_checked', 12345)
        self.assertEqual(12345, self.config.last_checked)
        self.config.reset_update_check()
        self.assertEqual(100, self.config.last_checked)

    def test_last_checked_set(self):
        """Test that set works on the config."""
        self.assertEqual(0, self.config.last_checked)
        self.config.set('update.last_checked', 12345)
        self.assertEqual(12345, self.config.last_checked)
        self.config.last_checked = 54321
        self.assertEqual(54321, self.config.last_checked)

    def test_needs_update_check(self):
        """Test that set works on the config."""
        original_environ = os.environ['CI'] if 'CI' in os.environ else None
        if original_environ:
            del os.environ['CI']
        self._create_config(config={}, time_value=100)
        self.assertFalse(self.config.needs_update_check)

        # Check that it works with the CI environment variable.
        os.environ['CI'] = "True"
        self.assertFalse(self.config.needs_update_check)
        del os.environ['CI']

        # Reset the environment.
        if original_environ:
            os.environ['CI'] = original_environ

    def test_read_config(self):
        """Test that config files can be read and parsed."""

        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, rc_config.RC_FILE_NAME)
            wd_filename = os.path.join(
                temp_dir, '{}{}'.format(rc_config.RC_FILE_NAME, 'wd'))
            with open(filename, 'w') as config_file:
                config_file.write('test: true')
            with open(wd_filename, 'w') as config_file:
                config_file.write('work: true')

            self._create_config(
                config=None, filename=filename, wd_filename=wd_filename)

            self.assertTrue(self.config.get('test'))
            self.assertTrue(self.config.get('work'))

    def test_write_config(self):
        """Test that config files can be written and parsed."""

        with tempfile.TemporaryDirectory() as temp_dir:
            filename = os.path.join(temp_dir, rc_config.RC_FILE_NAME)
            self._create_config(config=None, filename=filename)
            self.config.set('test', True)
            self.config.write()
            with open(filename, 'r') as config_file:
                results = config_file.read()
            self.assertIn('test: true', results)
