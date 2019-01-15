"""Untag an object using convention based keys."""

import re
from boltons import iterutils


LOCALIZED_KEY_REGEX = re.compile(r'(.*)@([^@]+)$')


class Untag(object):
    """Untagging utility for locale and environment based untagging."""

    @staticmethod
    def untag(data, locale_identifier=None, params=None):
        """Untags fields, handling translation priority."""
        paths_to_keep_tagged = set()
        locale_identifier = str(locale_identifier)

        # When untagging the order of the keys isn't consistent. Sometimes the
        # tagged value is found but then is overwritten by the original value
        # since it is processed after the tagged version. Need to keep track of
        # untagged keys to make sure that they are not overwritten by the original.
        untagged_key_paths = set()

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
                param_regex = re.compile(
                    r'(.*)@({})\.([^@]+)$'.format('|'.join(params.keys())),
                    re.IGNORECASE)
                param_match = param_regex.match(key)
                if param_match:
                    untagged_key, param_key, param_value = param_match.groups()

                    # If the key has already been untagged, don't overwrite.
                    if (path, untagged_key) in untagged_key_paths:
                        return False

                    if not params[param_key]:
                        return False
                    result = params[param_key](
                        data, untagged_key, param_key, param_value, value,
                        locale_identifier=locale_identifier)
                    if result is not False:
                        # Don't let the original key overwrite the new value.
                        untagged_key_paths.add((path, untagged_key))
                    return result

            # Support <key>@<locale regex>: <value>.
            match = LOCALIZED_KEY_REGEX.match(key)
            if not match:
                if (path, key) in untagged_key_paths:
                    return False
                return key, value

            if not locale_identifier:
                return False

            untagged_key, locale_from_key = match.groups()

            # If the key has already been untagged, don't overwrite.
            if (path, untagged_key) in untagged_key_paths:
                return False

            # TODO: Once the translation process is able to correctly extract
            # the locale tagged extractions we need to prevent replacing.
            # # When marked for extraction when tagged it should be used as the
            # # translation value in the message catalog, not replace the value.
            # if marked_for_extraction:
            #     return False

            locale_regex = re.compile(
                r'^{}$'.format(locale_from_key), re.IGNORECASE)
            if not locale_regex.match(locale_identifier):
                return False

            # Don't let the original key overwrite the new value.
            untagged_key_paths.add((path, untagged_key))

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
        if not re.match(value_regex, self.value, re.IGNORECASE):
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
        if not re.match(value_regex, locale_identifier, re.IGNORECASE):
            return False
        return untagged_key, value

    @classmethod
    def from_pod(cls, pod, collection=None):
        """Shortcut from the pod and collection objects."""
        podspec_data = pod.yaml.get('localization', {}).get('groups', {})
        if collection:
            collection_data = collection.fields.get('localization', {}).get('groups', {})
        else:
            collection_data = {}
        return cls(podspec_data, collection_data)
