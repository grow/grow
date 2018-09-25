"""Tests for the document fields."""

import unittest
from grow.documents import document_fields


class DocumentFieldsTestCase(unittest.TestCase):
    """Tests for the document fields."""

    def test_contains(self):
        """Fields contains field."""
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEqual(True, 'foo' in doc_fields)
        self.assertEqual(False, 'bar' in doc_fields)

    def test_get(self):
        """Retrieve a field value."""
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEqual('bar', doc_fields['foo'])
        self.assertEqual('baz', doc_fields.get('bar', 'baz'))

    def test_get_item(self):
        """Retrieve a field using item reference."""
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEqual('bar', doc_fields['foo'])

        with self.assertRaises(KeyError):
            _ = doc_fields['bar']

    def test_len(self):
        """Len of fields."""
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
            'bar': 'baz',
        }, None)

        self.assertEqual(2, len(doc_fields))

    def test_keys(self):
        """Keys of fields."""
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
            'bar': 'baz',
        }, None)

        self.assertIn('foo', doc_fields.keys())
        self.assertIn('bar', doc_fields.keys())

    def test_update(self):
        """Test that updates properly overwrite and are untagged."""
        doc_fields = document_fields.DocumentFields({
            'foo@': 'bar',
        })
        self.assertEqual('bar', doc_fields['foo'])
        doc_fields.update({
            'foo@': 'bbq',
        })
        self.assertEqual('bbq', doc_fields['foo'])
