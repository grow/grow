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

    def test_untag(self):
        fields_to_test = {
            'title': 'value-none',
            'title@fr': 'value-fr',
            'list': [
                {
                    'list-item-title': 'value-none',
                    'list-item-title@fr': 'value-fr',
                },
            ],
            'sub-nested': {
                'sub-nested': {
                    'nested@': 'sub-sub-nested-value',
                },
            },
            'nested': {
                'nested-none': 'nested-value-none',
                'nested-title@': 'nested-value-none',
            },
            'nested@fr': {
                'nested-title@': 'nested-value-fr',
            },
            'list@de': [
                'list-item-de',
            ]
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'value-fr',
            'list': [{'list-item-title': 'value-fr'}, ],
            'nested': {'nested-title': 'nested-value-fr', },
            'sub-nested': {
                'sub-nested': {
                    'nested': 'sub-sub-nested-value',
                },
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr'))

        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'value-none',
            'list': ['list-item-de', ],
            'nested': {
                'nested-none': 'nested-value-none',
                'nested-title': 'nested-value-none',
            },
            'sub-nested': {
                'sub-nested': {
                    'nested': 'sub-sub-nested-value',
                },
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))

        fields_to_test = {
            'foo': 'bar-base',
            'foo@de': 'bar-de',
            'foo@fr': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
                'nested@fr': 'nested-fr',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-fr',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))

        fields_to_test = {
            'list': [
                {
                    'item': 'value-1',
                    'item@de': 'value-1-de',
                    'item@fr': 'value-1-fr',
                },
                {
                    'item': 'value-2',
                },
                {
                    'item@fr': 'value-3-fr',
                },
            ]
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                {
                    'item': 'value-1-fr',
                },
                {
                    'item': 'value-2',
                },
                {
                    'item': 'value-3-fr',
                },
            ]
        }, document_fields.DocumentFields.untag(fields, locale='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                {
                    'item': 'value-1-de',
                },
                {
                    'item': 'value-2',
                },
                {},
            ]
        }, document_fields.DocumentFields.untag(fields, locale='de'))
        self.assertDictEqual({
            'list': [
                {
                    'item': 'value-1',
                },
                {
                    'item': 'value-2',
                },
                {},
            ]
        }, document_fields.DocumentFields.untag(fields, locale='ja'))

        fields_to_test = {
            '$view': '/views/base.html',
            '$view@ja': '/views/base-ja.html',
            'qaz': 'qux',
            'qaz@ja': 'qux-ja',
            'qaz@de': 'qux-de',
            'qaz@ja': 'qux-ja',
            'foo': 'bar-base',
            'foo@en': 'bar-en',
            'foo@de': 'bar-de',
            'foo@ja': 'bar-ja',
            'nested': {
                'nested': 'nested-base',
                'nested@ja': 'nested-ja',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            '$view': '/views/base-ja.html',
            'qaz': 'qux-ja',
            'foo': 'bar-ja',
            'nested': {
                'nested': 'nested-ja',
            },
        }, document_fields.DocumentFields.untag(fields, locale='ja'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            '$view': '/views/base.html',
            'qaz': 'qux-de',
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))

        fields_to_test = {
            'foo@': 'bar',
            'foo@fr@': 'bar-fr',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar',
        }, document_fields.DocumentFields.untag(fields))
        self.assertDictEqual({
            'foo': 'bar',
        }, document_fields.DocumentFields.untag(fields, locale='de'))
        self.assertDictEqual({
            'foo': 'bar-fr',
        }, document_fields.DocumentFields.untag(fields, locale='fr'))

        fields_to_test = {
            'list@': [
                'value1',
                'value2',
                'value3',
            ],
            'list@fr': [
                'value1-fr',
                'value2-fr',
                'value3-fr',
            ],
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                'value1',
                'value2',
                'value3',
            ],
            'list@': [
                'value1',
                'value2',
                'value3',
            ],
        }, document_fields.DocumentFields.untag(fields, locale='de'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'list': [
                'value1-fr',
                'value2-fr',
                'value3-fr',
            ],
            'list@': [
                'value1-fr',
                'value2-fr',
                'value3-fr',
            ],
        }, document_fields.DocumentFields.untag(fields, locale='fr'))

        fields_to_test = {
            'nested1': {
                'list@': [
                    'value1',
                    'value2',
                    'value3',
                    'value4',
                ],
                'list@fr@': [
                    'value1-fr',
                    'value2-fr',
                    'value3-fr',
                ],
            },
            'nested2': {
                'list@': [
                    'value1',
                    'value2',
                ],
                'list@fr@': [
                    'value1-fr',
                    'value2-fr',
                ],
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested1': {
                'list': [
                    'value1',
                    'value2',
                    'value3',
                    'value4',
                ],
                'list@': [
                    'value1',
                    'value2',
                    'value3',
                    'value4',
                ],
            },
            'nested2': {
                'list': [
                    'value1',
                    'value2',
                ],
                'list@': [
                    'value1',
                    'value2',
                ],
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested1': {
                'list': [
                    'value1-fr',
                    'value2-fr',
                    'value3-fr',
                ],
                'list@': [
                    'value1-fr',
                    'value2-fr',
                    'value3-fr',
                ],
            },
            'nested2': {
                'list': [
                    'value1-fr',
                    'value2-fr',
                ],
                'list@': [
                    'value1-fr',
                    'value2-fr',
                ],
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr'))

    def test_untag_with_backwards_compatibility(self):
        fields_to_test = {
            'title@': 'foo',
            'nested': {
                'list@': [
                    'value1',
                ],
            },
            'list@': [
                'top-value1',
                'top-value2',
                'top-value3',
            ],
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'foo',
            'list': [
                'top-value1',
                'top-value2',
                'top-value3',
            ],
            'list@': [
                'top-value1',
                'top-value2',
                'top-value3',
            ],
            'nested': {
                'list': [
                    'value1',
                ],
                'list@': [
                    'value1',
                ],
            },
        }, document_fields.DocumentFields.untag(fields))

    def test_untag_with_regex(self):
        fields_to_test = {
            'foo': 'bar-base',
            'foo@de': 'bar-de',
            'foo@fr.*': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
                'nested@de_AT': 'nested-de',
                'nested@fr': 'nested-fr',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-fr',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr'))
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr_FR'))
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr_CA'))
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))
        self.assertDictEqual({
            'foo': 'bar-base',
            'nested': {
                'nested': 'nested-de',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de_AT'))

        fields_to_test = {
            'foo': 'bar-base',
            'foo@de': 'bar-de',
            'foo@fr|it': 'bar-any',
            'nested': {
                'nested': 'nested-base',
                'nested@fr|it': 'nested-any',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-any',
            'nested': {
                'nested': 'nested-any',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-any',
            'nested': {
                'nested': 'nested-any',
            },
        }, document_fields.DocumentFields.untag(fields, locale='it'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))

    def test_untag_with_trailing_extract(self):
        """Test that trailing @ used for extracting does not interfere with untag."""
        fields_to_test = {
            'foo@': 'bar-base',
            'foo@de@': 'bar-de',
            'foo@(.*_FR|.*_SG)@': 'bar-fr',
            'nested': {
                'nested@': 'nested-base',
                'nested@de_AT@': 'nested-de',
                'nested@(.*_FR|.*_SG)@': 'nested-fr',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-base',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr'))
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-fr',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr_FR'))
        self.assertDictEqual({
            'foo': 'bar-base',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr_CA'))
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))
        self.assertDictEqual({
            'foo': 'bar-base',
            'nested': {
                'nested': 'nested-de',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de_AT'))

    def test_untag_with_no_base(self):
        """Test that not having a base key does not interfere with untag and locales."""
        fields_to_test = {
            'foo@de': 'bar-de',
            'baz@de': {
                'fum@de': 'boo-de'
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({}, document_fields.DocumentFields.untag(fields))
        self.assertDictEqual({
            'foo': 'bar-de',
            'baz': {
                'fum': 'boo-de',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))

    def test_untag_params(self):
        untag = document_fields.DocumentFields.untag
        fields_to_test = {
            'foo': 'base',
            'foo@env.dev': 'dev',
            'foo@env.prod': 'prod',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag(fields, locale=None, params={'env': None}))
        self.assertDictEqual({
            'foo': 'dev',
        }, untag(fields, locale=None, params={'env': 'dev'}))
        self.assertDictEqual({
            'foo': 'prod',
        }, untag(fields, locale=None, params={'env': 'prod'}))
        fields_to_test = {
            'nested': {
                'foo': 'nested-base',
            },
            'nested@de': {
                'foo': 'nested-de-base',
                'foo@env.dev': 'nested-de-dev',
                'foo@env.prod': 'nested-de-prod',
            }
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-base',
            },
        }, untag(fields, locale=None, params={'env': None}))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-base',
            },
        }, untag(fields, locale=None, params={'env': 'dev'}))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-de-dev',
            },
        }, untag(fields, locale='de', params={'env': 'dev'}))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-de-prod',
            },
        }, untag(fields, locale='de', params={'env': 'prod'}))

    def test_untag_none(self):
        """Untag when there is a none value for the tagged value."""
        untag = document_fields.DocumentFields.untag
        fields_to_test = {
            'foo': 'base',
            'foo@env.prod': None,
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag(fields, locale=None, params={'env': None}))
        self.assertDictEqual({
            'foo': None,
        }, untag(fields, locale=None, params={'env': 'prod'}))

        fields_to_test = {
            'nested': {
                'foo': 'nested-base',
            },
            'nested@de': {
                'foo': 'nested-de-base',
                'foo@env.prod': None,
            }
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-base',
            },
        }, untag(fields, locale=None, params={'env': None}))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-base',
            },
        }, untag(fields, locale=None, params={'env': 'dev'}))
        self.assertDictEqual({
            'nested': {
                'foo': None,
            },
        }, untag(fields, locale='de', params={'env': 'prod'}))

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
