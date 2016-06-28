from . import google_drive
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import cStringIO
import csv
import json
import unittest
import yaml


class GoogleSheetsPreprocessorTest(unittest.TestCase):

    def test_convert_rows_to_mapping(self):
        rows = [
            ['# Comment', True],
            ['foo.bar.baz', True],
            ['foo.bar.bam', True],
            ['foo.baz', True],
            ['qaz', True],
        ]
        expected = {
            'foo': {
                'bar': {
                    'baz': True,
                    'bam': True,
                },
                'baz': True,
            },
            'qaz': True,
        }
        preprocessor = google_drive.GoogleSheetsPreprocessor
        result = preprocessor._convert_rows_to_mapping(rows)
        self.assertDictEqual(expected, result)

    def test_format_content(self):
        rows = [
            ['key', 'value'],
            ['name', 'alice'],
            ['color', 'red'],
        ]
        fp = cStringIO.StringIO()
        writer = csv.writer(fp)
        for row in rows:
            writer.writerow(row)
        fp.seek(0)
        content_dict = dict(rows)
        content = fp.read()

        # Verify yaml.
        path = '/content/pages/test.yaml'
        result = google_drive.GoogleSheetsPreprocessor.format_content(
            content=content, path=path, format_as='map')
        self.assertEqual(content_dict, result)
        serialized_result = \
            google_drive.GoogleSheetsPreprocessor.serialize_content(
                formatted_data=result, path=path)
        expected = yaml.safe_dump(content_dict, default_flow_style=False)
        self.assertEqual(expected, serialized_result)

        # Verify json.
        path = '/content/pages/test.json'
        result = google_drive.GoogleSheetsPreprocessor.format_content(
            content=content, path=path, format_as='map')
        self.assertEqual(content_dict, result)
        serialized_result = \
            google_drive.GoogleSheetsPreprocessor.serialize_content(
                formatted_data=result, path=path)
        expected = json.dumps(content_dict)
        self.assertEqual(expected, serialized_result)

    def test_serialize_content(self):
        path = '/content/pages/test.json'
        formatted_data = {'key': 'value'}
        expected = json.dumps(formatted_data)
        result = google_drive.GoogleSheetsPreprocessor.serialize_content(
            formatted_data=formatted_data, path=path)
        self.assertEqual(expected, result)

        path = '/content/pages/test.yaml'
        formatted_data = {'key': 'value'}
        expected = yaml.safe_dump(formatted_data, default_flow_style=False)
        result = google_drive.GoogleSheetsPreprocessor.serialize_content(
            formatted_data=formatted_data, path=path)
        self.assertEqual(expected, result)

        path = '/content/pages/test.csv'
        formatted_data = 'key,value\n1,2\n'
        result = google_drive.GoogleSheetsPreprocessor.serialize_content(
            formatted_data=formatted_data, path=path)
        self.assertEqual(formatted_data, result)


if __name__ == '__main__':
    unittest.main()
