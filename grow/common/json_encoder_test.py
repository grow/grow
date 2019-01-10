"""Tests for custom JSON encoder."""

import datetime
import json
import unittest
from grow.documents import document_fields
from grow.pods import pods
from grow import storage
from grow.testing import testing
from . import json_encoder


class GrowJSONEncoderTestCase(unittest.TestCase):
    """Test the Grow JSONEncoder."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_datetime(self):
        """Test that datetime objects correctly serialize."""
        raw_date = datetime.datetime(2020, 12, 11, 10, 9, 8, 7)
        self.assertEqual('"2020-12-11T10:09:08.000007"', json.dumps(
            raw_date, cls=json_encoder.GrowJSONEncoder))

    def test_document(self):
        """Test that documents correctly serialize."""
        doc = self.pod.get_doc('/content/pages/text.txt')
        self.assertEqual('{"$title": "Text Page", "$hidden": true}', json.dumps(
            doc, cls=json_encoder.GrowJSONEncoder))

    def test_document_fields(self):
        """Test that document fields correctly serialize."""
        fields = document_fields.DocumentFields({'foo': 'bar', 'bar': True})
        self.assertEqual('{"foo": "bar", "bar": true}', json.dumps(
            fields, cls=json_encoder.GrowJSONEncoder))
