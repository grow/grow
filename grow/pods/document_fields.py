"""
Document fields for accessing the meta fields parsed from the document.
"""

from boltons import iterutils
import re


LOCALIZED_KEY_REGEX = re.compile('(.*)@([^@]+)$')


class DocumentFields(object):

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __init__(self, data, locale_identifier):
        self._data = DocumentFields._untag(data, locale_identifier)

    def __len__(self):
        return len(self._data)

    @staticmethod
    def _untag(data, locale=None):
        """Untags fields, handling translation priority."""

        updated_localized_paths = set()
        paths_to_keep_tagged = set()

        def visit(path, key, value):
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
        self._data.update(updated)
