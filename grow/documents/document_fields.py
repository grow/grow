"""Document fields for accessing the meta fields parsed from the document."""

import re
from boltons import iterutils


LOCALIZED_KEY_REGEX = re.compile(r'(.*)@([^@]+)$')


class DocumentFields(object):

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __init__(self, data, locale_identifier=None, params=None):
        self._locale_identifier = locale_identifier
        self._params = params
        self._data = DocumentFields.untag(
            data, locale_identifier, params=params)

    def __len__(self):
        return len(self._data)

    @staticmethod
    def untag(data, locale=None, params=None):
        """Untags fields, handling translation priority."""
        updated_localized_paths = set()
        paths_to_keep_tagged = set()

        def visit(path, key, value):
            """Function for each key and value in the data."""
            if not isinstance(key, basestring):
                return key, value
            if (path, key.rstrip('@')) in updated_localized_paths:
                return False
            if key.endswith('@#'):
                return False
            if key.endswith('@'):
                if isinstance(value, list):
                    paths_to_keep_tagged.add((path, key))
                key = key[:-1]

            # Support <key>@<param key>.<param value>: <value>.
            if params:
                param_regex = re.compile(
                    r'(.*)@({})\.([^@]+)$'.format('|'.join(params.keys())))
                param_match = param_regex.match(key)
                if param_match:
                    untagged_key, param_key, param_value = param_match.groups()
                    param_value_regex = r'^{}$'.format(param_value)
                    if not params[param_key] or not re.match(param_value_regex, params[param_key]):
                        return False
                    updated_localized_paths.add((path, untagged_key.rstrip('@')))
                    return untagged_key, value

            # Support <key>@<locale regex>: <value>.
            match = LOCALIZED_KEY_REGEX.match(key)
            if not match:
                updated_localized_paths.add((path, key))
                return key, value
            untagged_key, locale_from_key = match.groups()
            locale_regex = r'^{}$'.format(locale_from_key)
            if not locale or not re.match(locale_regex, locale):
                return False
            updated_localized_paths.add((path, untagged_key.rstrip('@')))
            return untagged_key, value

        # Backwards compatibility for https://github.com/grow/grow/issues/95
        def exit(path, key, old_parent, new_parent, new_items):
            resp = iterutils.default_exit(path, key, old_parent,
                                          new_parent, new_items)
            if paths_to_keep_tagged and isinstance(resp, dict):
                for sub_key, value in resp.items():
                    if not isinstance(value, list):
                        continue
                    new_key = '{}@'.format(sub_key)
                    resp[new_key] = value
                try:
                    paths_to_keep_tagged.remove((path, key))
                except KeyError:
                    pass
            return resp

        return iterutils.remap(data, visit=visit, exit=exit)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def update(self, updated):
        updated = DocumentFields.untag(
            updated, self._locale_identifier, params=self._params)
        self._data.update(updated)
