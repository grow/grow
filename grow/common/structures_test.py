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


class DeepReferenceDictTestCase(unittest.TestCase):
    """Test the deep reference dict structure."""

    def test_deep_reference(self):
        """Delimited keys are accessible."""
        obj = structures.DeepReferenceDict({
            'key': {
                'sub_key': {
                    'value': 'foo',
                }
            },
        })
        self.assertEqual('foo', obj['key']['sub_key']['value'])
        self.assertEqual('foo', obj['key.sub_key.value'])

    def test_deep_reference_error(self):
        """Missing keys raise error."""
        obj = structures.DeepReferenceDict({
            'key': {},
        })
        with self.assertRaises(KeyError):
            _ = obj['key.sub_key.value']

class SortedCollectionTestCase(unittest.TestCase):
    """Test the sorted collection structure."""

    def setUp(self):
        self.key = itemgetter(2)
        self.coll = structures.SortedCollection(key=self.key)
        for record in [
                ('roger', 'young', 30),
                ('angela', 'jones', 28),
                ('bill', 'smith', 22),
                ('david', 'thomas', 32)]:
            self.coll.insert(record)

    def test_clear(self):
        """Clears the collection."""
        self.assertEqual(4, len(self.coll))
        self.coll.clear()
        self.assertEqual(0, len(self.coll))

    def test_contains(self):
        """Contains matches."""
        self.assertTrue(('roger', 'young', 30) in self.coll)
        self.assertFalse(('bob', 'young', 30) in self.coll)

    def test_copy(self):
        """Copies the collection."""
        coll_copy = self.coll.copy()
        self.assertEqual(4, len(self.coll))
        self.assertEqual(4, len(coll_copy))
        self.coll.insert(('roger', 'young', 30))
        self.assertEqual(5, len(self.coll))
        self.assertEqual(4, len(coll_copy))

    def test_count(self):
        """Counts matches."""
        self.assertEqual(1, self.coll.count(('roger', 'young', 30)))
        self.coll.insert(('roger', 'young', 30))
        self.assertEqual(2, self.coll.count(('roger', 'young', 30)))

    def test_find(self):
        """Find first match."""
        self.assertEqual(('angela', 'jones', 28), self.coll.find(28))

        with self.assertRaises(ValueError):
            self.coll.find(39)

    def test_get_item(self):
        """Greater than equal."""
        self.assertEqual(('bill', 'smith', 22), self.coll[0])

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

    def test_insert_right(self):
        """Index from item."""
        self.assertEqual(1, self.coll.count(('roger', 'young', 30)))
        self.coll.insert_right(('roger', 'young', 30))
        self.assertEqual(2, self.coll.count(('roger', 'young', 30)))

    def test_key(self):
        """Index from item."""
        self.assertEqual(self.key, self.coll.key)
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

    def test_remove(self):
        """Removes matches."""
        item = ('roger', 'young', 30)
        self.assertTrue(item in self.coll)
        self.coll.remove(item)
        self.assertFalse(item in self.coll)

    def test_repr(self):
        """Output of repr."""
        actual = repr(self.coll)
        self.assertIn('SortedCollection(', actual)
        self.assertIn("('bill', 'smith', 22)", actual)
        self.assertIn("('angela', 'jones', 28)", actual)
        self.assertIn("('roger', 'young', 30)", actual)
        self.assertIn("('david', 'thomas', 32)", actual)

    def test_sorting(self):
        """Collection is sorted."""
        self.assertEqual([('bill', 'smith', 22),
                          ('angela', 'jones', 28),
                          ('roger', 'young', 30),
                          ('david', 'thomas', 32)], list(self.coll))
