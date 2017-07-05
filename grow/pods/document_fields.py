"""
Document fields for accessing the meta fields parsed from the document.
"""

from boltons import iterutils
import re


ENV_KEY_REGEX = re.compile('(.*)@env\.([^@]+)$')
LOCALIZED_KEY_REGEX = re.compile('(.*)@([^@]+)$')


class DocumentFields(object):

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __init__(self, data, locale_identifier=None, env_name=None):
        self._data = DocumentFields.untag(data, locale_identifier, env_name)

    def __len__(self):
        return len(self._data)

    @staticmethod
    def untag(data, locale=None, env_name=None):
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
            # Support <key>@env.<name regex>: <value>.
            env_match = ENV_KEY_REGEX.match(key)
            if env_match:
                untagged_key, env_name_from_key = env_match.groups()
                env_regex = r'^{}$'.format(env_name_from_key)
                if not env_name or not re.match(env_regex, env_name):
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
        self._data.update(updated)
