"""Tests for the document fields."""

import copy
import unittest
from grow.documents import document_fields


class DocumentFieldsTestCase(unittest.TestCase):

    def testContains(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEqual(True, 'foo' in doc_fields)
        self.assertEqual(False, 'bar' in doc_fields)

    def testGet(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEqual('bar', doc_fields['foo'])
        self.assertEqual('baz', doc_fields.get('bar', 'baz'))

    def testGetItem(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEqual('bar', doc_fields['foo'])

        with self.assertRaises(KeyError):
            doc_fields['bar']

    def testLen(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
            'bar': 'baz',
        }, None)

        self.assertEqual(2, len(doc_fields))

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


if __name__ == '__main__':
    unittest.main()
