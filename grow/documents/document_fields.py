"""Document fields for accessing the meta fields parsed from the document."""

import re
from grow.common import untag


LOCALIZED_KEY_REGEX = re.compile(r'(.*)@([^@]+)$')


class DocumentFields(object):

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __init__(self, data, locale_identifier=None, params=None):
        self._locale_identifier = locale_identifier
        self._params = params
        self._data = untag.Untag.untag(
            data, locale_identifier, params=params)

    def __len__(self):
        return len(self._data)

    def __repr__(self):
        return "<DocumentFields(locale='{}')>".format(self._locale_identifier)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def keys(self):
        return self._data.keys()

    def update(self, updated):
        updated = untag.Untag.untag(
            updated, self._locale_identifier, params=self._params)
        self._data.update(updated)
