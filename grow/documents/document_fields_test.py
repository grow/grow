"""Tests for the document fields."""

import copy
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

    def test_untag_simple(self):
        """Untag field values by locale with nested fields."""
        fields_to_test = {
            '$view': '/views/base.html',
            '$view@ja': '/views/base-ja.html',
            'qaz': 'qux',
            'qaz@ja': 'qux-ja',
            'qaz@de': 'qux-de',
            'foo': 'bar-base',
            'foo@en': 'bar-en',
            'foo@de': 'bar-de',
            'foo@ja': 'bar-ja',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            '$view': '/views/base-ja.html',
            'qaz': 'qux-ja',
            'foo': 'bar-ja',
        }, document_fields.DocumentFields.untag(fields, locale='ja'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            '$view': '/views/base.html',
            'qaz': 'qux-de',
            'foo': 'bar-de',
        }, document_fields.DocumentFields.untag(fields, locale='de'))

    def test_untag_nested(self):
        """Untag field values by locale with nested fields."""
        fields_to_test = {
            'nested': {
                'nested': 'nested-base',
                'nested@fr': 'nested-fr',
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested': {
                'nested': 'nested-fr',
            },
        }, document_fields.DocumentFields.untag(fields, locale='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested': {
                'nested': 'nested-base',
            },
        }, document_fields.DocumentFields.untag(fields, locale='de'))

    def test_untag_list(self):
        """Untag field values by locale with lists."""
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

    def test_untag_list_nested(self):
        """Untag field values by locale with nested list fields."""
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

    # pylint: disable=invalid-name
    def test_untag_backwards_compatibility(self):
        """Test backwards compatibility with untagging."""
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
        """Test that regex works with the untagging keys."""
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

    def test_untag_with_regex_or(self):
        """Test that regex works with the untagging keys."""
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
        """Untag params in fields."""
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

    def test_untag_params_nested(self):
        """Untag params in nested fields."""
        untag = document_fields.DocumentFields.untag
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

    def test_untag_translation(self):
        """Untag when tagged for translation.

        When untagging a locale that has a trailing @ it is used as the
        translated value for the key, not as the actual value untagged.

        This makes it so that translated values are done as translations so
        gettext works correctly in templates.

        See https://docs.google.com/document/d/19rFeAdIjO6mHJG8p8MuOHy5ywG4bYD3FlLdH81dH5Og/
        """
        untag = document_fields.DocumentFields.untag
        fields_to_test = {
            'foo@': 'base',
            'foo@fr@': 'fr',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag(fields, locale=None))
        self.assertDictEqual({
            'foo': 'base',
        }, untag(fields, locale='fr'))

    def test_untag_translation_comment(self):
        """Untag ignored translation comments."""
        untag = document_fields.DocumentFields.untag
        fields_to_test = {
            'bar@#': 'comment',
            'foo@': 'base',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag(fields, locale=None))

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
