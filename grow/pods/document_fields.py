"""
Document fields for accessing the meta fields parsed from the document.
"""


class DocumentFields(object):

    def __contains__(self, item):
        return item in self._data

    def __getitem__(self, key):
        return self._data[key]

    def __init__(self, doc, data, locale_identifier):
        self._doc = doc
        self._data = data
        self._locale_identifier = locale_identifier

    def __len__(self):
        return len(self._data)

    def get(self, key, default=None):
        return self._data.get(key, default)
