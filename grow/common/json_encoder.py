"""Custom json encoder for handling Grow classes."""

import datetime
import json

from grow.documents import document, document_fields


class GrowJSONEncoder(json.JSONEncoder):
    """Encoder for serializing Grow objects."""

    def default(self, o):
        """Attempt to encode known objects."""
        if isinstance(o, datetime.date):
            return o.isoformat()

        if isinstance(o, datetime.datetime):
            return o.isoformat()

        if isinstance(o, document.Document):
            return o.fields._data

        if isinstance(o, document_fields.DocumentFields):
            return o._data

        if isinstance(o, set):
            return list(o)

        return json.JSONEncoder.default(self, o)
