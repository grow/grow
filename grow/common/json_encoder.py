"""Custom json encoder for handling Grow classes."""

import datetime
import json
from grow.pods import document_fields
from grow.pods import documents


class GrowJSONEncoder(json.JSONEncoder):
    """Encoder for serializing Grow objects."""

    # pylint: disable=method-hidden
    def default(self, o):
        """Attempt to encode known objects."""
        if isinstance(o, datetime.datetime):
            return o.isoformat()

        if isinstance(o, documents.Document):
            # pylint: disable=protected-access
            return o.fields._data

        if isinstance(o, document_fields.DocumentFields):
            # pylint: disable=protected-access
            return o._data

        return json.JSONEncoder.default(self, o)
