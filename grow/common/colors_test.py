"""Tests for colors."""

import unittest
from grow.common import colors


class ColorsTestCase(unittest.TestCase):
    """Test the terminal colors."""

    def test_caution(self):
        """Consistent color for caution."""
        self.assertEqual('\x1b[38;5;3m\x1b[1m', colors.CAUTION)

    def test_error(self):
        """Consistent color for error."""
        self.assertEqual('\x1b[38;5;1m\x1b[1m', colors.ERROR)

    def test_emphasis(self):
        """Consistent color for emphasis."""
        self.assertEqual('\x1b[38;5;130m', colors.EMPHASIS)

    def test_hightlight(self):
        """Consistent color for hightlight."""
        self.assertEqual('\x1b[38;5;10m', colors.HIGHLIGHT)

    def test_success(self):
        """Consistent color for success."""
        self.assertEqual('\x1b[38;5;2m\x1b[1m', colors.SUCCESS)
