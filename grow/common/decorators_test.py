"""Tests for decorators."""

import unittest
from grow.common import decorators


class DecoratorsTestCase(unittest.TestCase):
    """Test the grow decorators."""

    def test_non_memoize(self):
        """Test that non memoize changes results."""
        return_value = 'pepperoni'

        def _topping():
            return return_value

        self.assertEqual('pepperoni', _topping())
        return_value = 'cheese'
        self.assertEqual('cheese', _topping())

    def test_memoize(self):
        """Test that memoize uses first result."""
        return_value = 'pepperoni'

        @decorators.Memoize
        def _topping():
            return return_value

        self.assertEqual('pepperoni', _topping())
        return_value = 'cheese'
        self.assertEqual('pepperoni', _topping())

    def test_memoize_tag(self):
        """Test that memoize uses first result."""
        return_value = 'pepperoni'

        @decorators.MemoizeTag
        def _topping(**_kwargs):
            return return_value

        self.assertEqual('pepperoni', _topping())
        return_value = 'cheese'
        self.assertEqual('pepperoni', _topping())
        self.assertEqual('cheese', _topping(use_cache=False))
