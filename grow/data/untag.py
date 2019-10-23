"""Untag an object using convention based keys."""

import re
from boltons import iterutils


LOCALIZED_KEY_REGEX = re.compile(r'(.*)@([^@]+)$')
PARAM_KEY_REGEX_TEMPLATE = r'(.*)@({})\.([^@]+)$'


class Untag(object):
    """Untagging utility for locale and environment based untagging."""

    @staticmethod
    def untag(data, locale_identifier=None, params=None):
        """Untags fields, handling translation priority."""
        data = data or {}
        paths_to_keep_tagged = set()

        # pylint: disable=too-many-return-statements
        def _visit(path, key, value):
            """Function for each key and value in the data."""
            if not isinstance(key, str):
                return key, value

            if key.endswith('@#'):
                # Translation Comment.
                return False

            marked_for_extraction = key.endswith('@')
            if marked_for_extraction:
                if isinstance(value, list):
                    paths_to_keep_tagged.add((path, key))
                key = key[:-1]

            # Support <key>@<param key>.<param value>: <value>.
            if params:
                param_regex = re.compile(PARAM_KEY_REGEX_TEMPLATE.format(
                    '|'.join(params.keys())))
                param_match = param_regex.match(key)
                if param_match:
                    untagged_key, param_key, param_value = param_match.groups()
                    if not params[param_key]:
                        return False
                    return params[param_key](
                        data, untagged_key, param_key, param_value, value,
                        locale_identifier=locale_identifier)

            # Support <key>@<locale regex>: <value>.
            match = LOCALIZED_KEY_REGEX.match(key)
            if not match:
                return key, value
            untagged_key, locale_from_key = match.groups()
            locale_regex = r'^{}$'.format(locale_from_key)
            if marked_for_extraction or not locale_identifier or not re.match(locale_regex, locale_identifier):
                return False

            return untagged_key, value

        # Backwards compatibility for https://github.com/grow/grow/issues/95
        def _remap_exit(path, key, old_parent, new_parent, new_items):
            resp = iterutils.default_exit(path, key, old_parent,
                                          new_parent, new_items)
            if paths_to_keep_tagged and isinstance(resp, dict):
                updated_values = {}
                for sub_key, value in resp.items():
                    if not isinstance(value, list):
                        continue
                    new_key = '{}@'.format(sub_key)
                    updated_values[new_key] = value
                resp.update(updated_values)
                try:
                    paths_to_keep_tagged.remove((path, key))
                except KeyError:
                    pass
            return resp

        return iterutils.remap(data, visit=_visit, exit=_remap_exit)


class UntagParam(object):
    """Untagging param for complex untagging."""

    def __call__(self, data, untagged_key, param_key, param_value, value, locale_identifier=None):
        raise NotImplementedError()


class UntagParamRegex(object):
    """Param using the value of the param value as a regex to match."""

    def __init__(self, value):
        self.value = value

    def __call__(self, data, untagged_key, param_key, param_value, value, locale_identifier=None):
        if not self.value:
            return False
        value_regex = r'^{}$'.format(param_value)
        if not re.match(value_regex, self.value):
            return False
        return untagged_key, value


class UntagParamLocaleRegex(object):
    """Param using a document field as a regex group to match locale.

    Attempts to use the value of one of the other data fields as a locale regex.
    If there is no matching key found it falls back to the collection or podspec.
    """

    def __init__(self, podspec_data=None, collection_data=None):
        self.podspec_data = podspec_data or {}
        self.collection_data = collection_data or {}

    def __call__(self, data, untagged_key, param_key, param_value, value, locale_identifier=None):
        podspec_value = self.podspec_data.get(param_value, None)
        collection_value = self.collection_data.get(param_value, podspec_value)
        local_groups = data.get('$localization', {}).get('groups', {})
        regex_value = local_groups.get(param_value, collection_value)
        if not regex_value:
            return False

        # Convert lists of locales into a regex pattern.
        if not isinstance(regex_value, str):
            regex_value = '|'.join(regex_value)

        value_regex = r'^{}$'.format(regex_value)
        if not re.match(value_regex, locale_identifier):
            return False
        return untagged_key, value
