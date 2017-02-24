import unittest

from . import document_fields


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

if __name__ == '__main__':
    unittest.main()
