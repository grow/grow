"""Tests for the common utility methods."""

import unittest
from grow.common import formatting


class FormattingTestCase(unittest.TestCase):
    """Test the custom formatters."""

    def test_safe_format(self):
        """Use modern text formatting on a string safely."""
        actual = formatting.safe_format('Does it {0}?', 'work')
        self.assertEqual('Does it work?', actual)

        actual = formatting.safe_format('Does it {work}?', work='blend')
        self.assertEqual('Does it blend?', actual)

        actual = formatting.safe_format('Does it {ignore}?')
        self.assertEqual('Does it {ignore}?', actual)


if __name__ == '__main__':
    unittest.main()
