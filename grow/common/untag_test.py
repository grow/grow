"""Tests for the untagging."""

import copy
import unittest
from grow.common import untag


class UntagTestCase(unittest.TestCase):
    """Tests for the untagging."""

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
        }, untag.Untag.untag(fields, locale_identifier='ja'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            '$view': '/views/base.html',
            'qaz': 'qux-de',
            'foo': 'bar-de',
        }, untag.Untag.untag(fields, locale_identifier='de'))

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
        }, untag.Untag.untag(fields, locale_identifier='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'nested': {
                'nested': 'nested-base',
            },
        }, untag.Untag.untag(fields, locale_identifier='de'))

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
        }, untag.Untag.untag(fields, locale_identifier='fr'))
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
        }, untag.Untag.untag(fields, locale_identifier='de'))
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
        }, untag.Untag.untag(fields, locale_identifier='ja'))

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
        }, untag.Untag.untag(fields, locale_identifier='de'))
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
        }, untag.Untag.untag(fields, locale_identifier='fr'))

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
        }, untag.Untag.untag(fields))

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
        }, untag.Untag.untag(fields, locale_identifier='fr'))
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
            },
        }, untag.Untag.untag(fields, locale_identifier='fr_FR'))
        self.assertDictEqual({
            'foo': 'bar-fr',
            'nested': {
                'nested': 'nested-base',
            },
        }, untag.Untag.untag(fields, locale_identifier='fr_CA'))
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, untag.Untag.untag(fields, locale_identifier='de'))
        self.assertDictEqual({
            'foo': 'bar-base',
            'nested': {
                'nested': 'nested-de',
            },
        }, untag.Untag.untag(fields, locale_identifier='de_AT'))

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
        }, untag.Untag.untag(fields, locale_identifier='fr'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-any',
            'nested': {
                'nested': 'nested-any',
            },
        }, untag.Untag.untag(fields, locale_identifier='it'))
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'bar-de',
            'nested': {
                'nested': 'nested-base',
            },
        }, untag.Untag.untag(fields, locale_identifier='de'))

    def test_untag_with_no_base(self):
        """Test that not having a base key does not interfere with untag and locales."""
        fields_to_test = {
            'foo@de': 'bar-de',
            'baz@de': {
                'fum@de': 'boo-de'
            },
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({}, untag.Untag.untag(fields))
        self.assertDictEqual({
            'foo': 'bar-de',
            'baz': {
                'fum': 'boo-de',
            },
        }, untag.Untag.untag(fields, locale_identifier='de'))

    def test_untag_params_not_implemented(self):
        """Untag params in fields using base class."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            'foo': 'base',
            'foo@env.prod': 'prod',
        }
        with self.assertRaises(NotImplementedError):
            untag_func(fields_to_test, locale_identifier=None, params={
                'env': untag.UntagParam(),
            })

    def test_untag_params_none_callable(self):
        """Untag params in fields using none as the param."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            'foo': 'base',
            'foo@env.prod': 'prod',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag_func(fields, locale_identifier=None, params={
            'env': None,
        }))

    def test_untag_params(self):
        """Untag params in fields."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            'foo': 'base',
            'foo@env.dev': 'dev',
            'foo@env.prod': 'prod',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex(None),
        }))
        self.assertDictEqual({
            'foo': 'dev',
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex('dev'),
        }))
        self.assertDictEqual({
            'foo': 'prod',
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex('prod'),
        }))

    def test_untag_params_locale(self):
        """Untag locale group params in fields."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            '$localization': {
                'groups': {
                    'group1': 'fr|de',
                    'group2': 'es|ja',
                },
            },
            'foo': 'base',
            'foo@locale.group1': 'g1',
            'foo@locale.group2': 'g2',
        }
        fields = copy.deepcopy(fields_to_test)

        # Non-group locale.
        self.assertDictEqual({
            'foo': 'base',
            '$localization': {
                'groups': {
                    'group1': 'fr|de',
                    'group2': 'es|ja',
                },
            },
        }, untag_func(fields, locale_identifier='en', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))

        # Group 1
        self.assertDictEqual({
            'foo': 'g1',
            '$localization': {
                'groups': {
                    'group1': 'fr|de',
                    'group2': 'es|ja',
                },
            },
        }, untag_func(fields, locale_identifier='de', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))
        self.assertDictEqual({
            'foo': 'g1',
            '$localization': {
                'groups': {
                    'group1': 'fr|de',
                    'group2': 'es|ja',
                },
            },
        }, untag_func(fields, locale_identifier='fr', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))

        # Group 2
        self.assertDictEqual({
            'foo': 'g2',
            '$localization': {
                'groups': {
                    'group1': 'fr|de',
                    'group2': 'es|ja',
                },
            },
        }, untag_func(fields, locale_identifier='es', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))
        self.assertDictEqual({
            'foo': 'g2',
            '$localization': {
                'groups': {
                    'group1': 'fr|de',
                    'group2': 'es|ja',
                },
            },
        }, untag_func(fields, locale_identifier='ja', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))

    def test_untag_params_locale_list(self):
        """Untag locale group params in fields."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            '$localization': {
                'groups': {
                    'group1': ['fr', 'de'],
                },
            },
            'foo': 'base',
            'foo@locale.group1': 'g1',
        }
        fields = copy.deepcopy(fields_to_test)

        # Non-group locale.
        self.assertDictEqual({
            'foo': 'base',
            '$localization': {
                'groups': {
                    'group1': ['fr', 'de'],
                },
            },
        }, untag_func(fields, locale_identifier='en', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))

        # Group 1
        self.assertDictEqual({
            'foo': 'g1',
            '$localization': {
                'groups': {
                    'group1': ['fr', 'de'],
                },
            },
        }, untag_func(fields, locale_identifier='de', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))
        self.assertDictEqual({
            'foo': 'g1',
            '$localization': {
                'groups': {
                    'group1': ['fr', 'de'],
                },
            },
        }, untag_func(fields, locale_identifier='fr', params={
            'locale': untag.UntagParamLocaleRegex(),
        }))

    def test_untag_params_locale_fallback(self):
        """Untag locale group params in fields falls back to pod and collection."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            'foo': 'base',
            'foo@locale.group1': 'g1',
            'foo@locale.group2': 'g2',
        }
        podspec_data = {
            'group1': 'fr|de',
        }
        collection_data = {
            'group2': 'es|ja',
        }
        fields = copy.deepcopy(fields_to_test)

        # Non-group locale.
        self.assertDictEqual({
            'foo': 'base',
        }, untag_func(fields, locale_identifier='en', params={
            'locale': untag.UntagParamLocaleRegex(podspec_data, collection_data),
        }))

        # Group 1
        self.assertDictEqual({
            'foo': 'g1',
        }, untag_func(fields, locale_identifier='de', params={
            'locale': untag.UntagParamLocaleRegex(podspec_data, collection_data),
        }))
        self.assertDictEqual({
            'foo': 'g1',
        }, untag_func(fields, locale_identifier='fr', params={
            'locale': untag.UntagParamLocaleRegex(podspec_data, collection_data),
        }))

        # Group 2
        self.assertDictEqual({
            'foo': 'g2',
        }, untag_func(fields, locale_identifier='es', params={
            'locale': untag.UntagParamLocaleRegex(podspec_data, collection_data),
        }))
        self.assertDictEqual({
            'foo': 'g2',
        }, untag_func(fields, locale_identifier='ja', params={
            'locale': untag.UntagParamLocaleRegex(podspec_data, collection_data),
        }))

    def test_untag_params_locale_missing_group(self):
        """Untag locale group params without the group."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            'foo': 'base',
            'foo@locale.group1': 'g1',
        }
        podspec_data = {}
        collection_data = {}
        fields = copy.deepcopy(fields_to_test)

        # Non-group locale.
        self.assertDictEqual({
            'foo': 'base',
        }, untag_func(fields, locale_identifier='en', params={
            'locale': untag.UntagParamLocaleRegex(podspec_data, collection_data),
        }))

        # Missing group.
        self.assertDictEqual({
            'foo': 'base',
        }, untag_func(fields, locale_identifier='de', params={
            'locale': untag.UntagParamLocaleRegex(podspec_data, collection_data),
        }))

    def test_untag_params_nested(self):
        """Untag params in nested fields."""
        untag_func = untag.Untag.untag
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
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex(None),
        }))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-base',
            },
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex('dev'),
        }))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-de-dev',
            },
        }, untag_func(fields, locale_identifier='de', params={
            'env': untag.UntagParamRegex('dev'),
        }))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-de-prod',
            },
        }, untag_func(fields, locale_identifier='de', params={
            'env': untag.UntagParamRegex('prod'),
        }))

    def test_untag_none(self):
        """Untag when there is a none value for the tagged value."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            'foo': 'base',
            'foo@env.prod': None,
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex(None),
        }))
        self.assertDictEqual({
            'foo': None,
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex('prod'),
        }))

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
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex(None),
        }))
        self.assertDictEqual({
            'nested': {
                'foo': 'nested-base',
            },
        }, untag_func(fields, locale_identifier=None, params={
            'env': untag.UntagParamRegex('dev'),
        }))
        self.assertDictEqual({
            'nested': {
                'foo': None,
            },
        }, untag_func(fields, locale_identifier='de', params={
            'env': untag.UntagParamRegex('prod'),
        }))

    # TODO: Once the translation process is able to correctly extract
    # the locale tagged extractions we need to prevent replacing the value.
    # def test_untag_translation(self):
    #     """Untag when tagged for translation.
    #
    #     When untagging a locale that has a trailing @ it is used as the
    #     translated value for the key, not as the actual value untagged.
    #
    #     This makes it so that translated values are done as translations so
    #     gettext works correctly in templates.
    #
    #     See https://docs.google.com/document/d/19rFeAdIjO6mHJG8p8MuOHy5ywG4bYD3FlLdH81dH5Og/
    #     """
    #     untag_func = untag.Untag.untag
    #     fields_to_test = {
    #         'foo@': 'base',
    #         'foo@fr@': 'fr',
    #     }
    #     fields = copy.deepcopy(fields_to_test)
    #     self.assertDictEqual({
    #         'foo': 'base',
    #     }, untag_func(fields, locale_identifier=None))
    #     self.assertDictEqual({
    #         'foo': 'base',
    #     }, untag_func(fields, locale_identifier='fr'))

    def test_untag_translation_comment(self):
        """Untag ignored translation comments."""
        untag_func = untag.Untag.untag
        fields_to_test = {
            'bar@#': 'comment',
            'foo@': 'base',
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'foo': 'base',
        }, untag_func(fields, locale_identifier=None))
