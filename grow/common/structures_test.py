"""Tests for structures."""

import unittest
from grow.common import structures
from operator import itemgetter


class AttributeDictTestCase(unittest.TestCase):
    """Test the attribute dict structure."""

    def test_attributes(self):
        """Keys are accessible as attributes."""
        obj = structures.AttributeDict({
            'key': 'value',
        })
        self.assertEqual('value', obj['key'])
        self.assertEqual('value', obj.key)


class SortedCollectionTestCase(unittest.TestCase):
    """Test the sorted collection structure."""

    def setUp(self):
        self.coll = structures.SortedCollection(key=itemgetter(2))
        for record in [
                ('roger', 'young', 30),
                ('angela', 'jones', 28),
                ('bill', 'smith', 22),
                ('david', 'thomas', 32)]:
            self.coll.insert(record)

    def test_ge(self):
        """Greater than equal."""
        self.assertEqual(('angela', 'jones', 28), self.coll.find_ge(28))

        with self.assertRaises(ValueError):
            self.coll.find_ge(40)

    def test_gt(self):
        """Greater than."""
        self.assertEqual(('roger', 'young', 30), self.coll.find_gt(28))

        with self.assertRaises(ValueError):
            self.coll.find_gt(40)

    def test_index(self):
        """Index from item."""
        match = self.coll.find_gt(28)
        self.assertEqual(2, self.coll.index(match))

    def test_key(self):
        """Index from item."""
        self.coll.key = itemgetter(0)  # now sort by first name
        self.assertEqual([('angela', 'jones', 28),
                          ('bill', 'smith', 22),
                          ('david', 'thomas', 32),
                          ('roger', 'young', 30)], list(self.coll))

    def test_le(self):
        """Less than equal."""
        self.assertEqual(('angela', 'jones', 28), self.coll.find_le(28))

        with self.assertRaises(ValueError):
            self.coll.find_le(10)

    def test_lt(self):
        """Less than."""
        self.assertEqual(('bill', 'smith', 22), self.coll.find_lt(28))

        with self.assertRaises(ValueError):
            self.coll.find_lt(10)

    def test_sorting(self):
        """Collection is sorted."""
        self.assertEqual([('bill', 'smith', 22),
                          ('angela', 'jones', 28),
                          ('roger', 'young', 30),
                          ('david', 'thomas', 32)], list(self.coll))
