"""Custom json encoder for handling Grow classes."""

import datetime
import json
from grow.documents import document
from grow.documents import document_fields


class GrowJSONEncoder(json.JSONEncoder):
    """Encoder for serializing Grow objects."""

    # pylint: disable=method-hidden
    def default(self, o):
        """Attempt to encode known objects."""
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        if isinstance(o, document.Document):
            # pylint: disable=protected-access
            return o.fields._data

        if isinstance(o, document_fields.DocumentFields):
            # pylint: disable=protected-access
            return o._data

        return json.JSONEncoder.default(self, o)
