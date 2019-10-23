"""Tests for system utilities."""

import sys
import unittest
from grow.common import system


class SystemTestCase(unittest.TestCase):
    """Test the system utilities."""

    def test_is_packaged_app(self):
        """Test that it detects packaged apps correctly."""
        # pylint: disable=protected-access
        try:
            original_meipass = sys._MEIPASS
        except AttributeError:
            original_meipass = None

        try:
            if original_meipass:
                del sys._MEIPASS
            self.assertFalse(system.is_packaged_app())

            # Check that it works with the CI environment variable.
            sys._MEIPASS = True
            self.assertTrue(system.is_packaged_app())
            del sys._MEIPASS
        finally:
            # Reset the environment.
            if original_meipass:
                sys._MEIPASS = original_meipass
