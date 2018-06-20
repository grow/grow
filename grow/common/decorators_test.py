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
            """Toppings!"""
            return return_value

        self.assertEqual('Toppings!', repr(_topping))

        self.assertEqual('pepperoni', _topping())
        return_value = 'cheese'
        self.assertEqual('pepperoni', _topping())

        _topping.reset()
        self.assertEqual('cheese', _topping())

    def test_memoize_property(self):
        """Test that memoize works with __get__."""
        return_value = 'pepperoni'

        class Pizza(object):
            """PIZZA!"""
            @decorators.Memoize
            def topping(self):
                """Toppings!"""
                return return_value

        pizza = Pizza()

        self.assertEqual('pepperoni', pizza.topping)
        return_value = 'cheese'
        self.assertEqual('pepperoni', pizza.topping)

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
