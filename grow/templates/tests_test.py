"""Tests for the template tests."""

import unittest
from grow.templates import tests


class BuiltinTestsTestCase(unittest.TestCase):

    def test_subset_filter(self):
        """Provided value is a subset when has all the required values."""
        value = ['banana', 'apple']
        test_value = ['banana']
        self.assertTrue(tests.is_subset_of(value, test_value))

    def test_subset_filter_equal(self):
        """Provided value is a subset when equal."""
        value = ['banana']
        test_value = ['banana']
        self.assertTrue(tests.is_subset_of(value, test_value))

    def test_subset_filter_not(self):
        """Provided value is not a subset when missing values."""
        value = ['banana']
        test_value = ['banana', 'apple']
        self.assertFalse(tests.is_subset_of(value, test_value))

    def test_subset_filter_none(self):
        """Provided value is a subset when both are blank."""
        value = []
        test_value = []
        self.assertTrue(tests.is_subset_of(value, test_value))

    def test_superset_filter(self):
        """Provided value is a superset when missing some of the values."""
        value = ['banana']
        test_value = ['banana', 'apple']
        self.assertTrue(tests.is_superset_of(value, test_value))

    def test_superset_filter_equal(self):
        """Provided value is a superset when equal."""
        value = ['banana']
        test_value = ['banana']
        self.assertTrue(tests.is_superset_of(value, test_value))

    def test_superset_filter_not(self):
        """Provided value is not a superset when has extra values."""
        value = ['banana', 'apple']
        test_value = ['banana']
        self.assertFalse(tests.is_superset_of(value, test_value))

    def test_superset_filter_none(self):
        """Provided value is a superset when both are blank."""
        value = []
        test_value = []
        self.assertTrue(tests.is_superset_of(value, test_value))


if __name__ == '__main__':
    unittest.main()
