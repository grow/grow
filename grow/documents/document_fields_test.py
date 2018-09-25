"""Tests for the document fields."""

import copy
import unittest
from grow.documents import document_fields


class DocumentFieldsTestCase(unittest.TestCase):

    def testContains(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEquals(True, 'foo' in doc_fields)
        self.assertEquals(False, 'bar' in doc_fields)

    def testGet(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEquals('bar', doc_fields['foo'])
        self.assertEquals('baz', doc_fields.get('bar', 'baz'))

    def testGetItem(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
        }, None)

        self.assertEquals('bar', doc_fields['foo'])

        with self.assertRaises(KeyError):
            doc_fields['bar']

    def testLen(self):
        doc_fields = document_fields.DocumentFields({
            'foo': 'bar',
            'bar': 'baz',
        }, None)

        self.assertEquals(2, len(doc_fields))

    def test_update(self):
        """Test that updates properly overwrite and are untagged."""
        doc_fields = document_fields.DocumentFields({
            'foo@': 'bar',
        })
        self.assertEquals('bar', doc_fields['foo'])
        doc_fields.update({
            'foo@': 'bbq',
        })
        self.assertEquals('bbq', doc_fields['foo'])


if __name__ == '__main__':
    unittest.main()
