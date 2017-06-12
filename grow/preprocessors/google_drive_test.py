"""Tests for Google Drive preprocessor."""

import cStringIO
import copy
import csv
import json
import unittest
import yaml
from grow.pods import pods
from grow.testing import testing
from . import google_drive


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

        # Verify key_to_update.
        path = '/content/pages/test.yaml'
        existing_data = copy.deepcopy(content_dict)
        result = google_drive.GoogleSheetsPreprocessor.format_content(
            content=content, path=path, existing_data=existing_data,
            format_as='map', key_to_update='address')
        serialized_result = \
            google_drive.GoogleSheetsPreprocessor.serialize_content(
                formatted_data=result, path=path)
        expected = copy.deepcopy(content_dict)
        expected['address'] = {
            'color': 'red',
            'key': 'value',
            'name': 'alice',
        }
        self.assertDictEqual(expected, result)

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

    def test_get_edit_url(self):
        pod = testing.create_pod()
        path = '/content/pages/home.yaml'
        pod.write_yaml(path, {})

        # Verify Google Sheets URLs.
        fields = {
            'preprocessors': [{
                'kind': 'google_sheets',
                'path': path,
                'id': '012345',
                'gid': '987654',
            }],
        }
        pod.write_yaml('/podspec.yaml', fields)
        doc = pod.get_doc(path)
        preprocessor = pod.list_preprocessors()[0]
        self.assertEqual('https://docs.google.com/spreadsheets/d/012345/edit#gid=987654',
                         preprocessor.get_edit_url(doc))

        # Verify Google Docs URLs.
        fields = {
            'preprocessors': [{
                'kind': 'google_docs',
                'path': path,
                'id': '012345',
            }],
        }
        pod.write_yaml('/podspec.yaml', fields)
        pod = pods.Pod(pod.root)  # Reset pod.list_preprocessors.
        preprocessor = pod.list_preprocessors()[0]
        self.assertEqual('https://docs.google.com/document/d/012345/edit',
                         preprocessor.get_edit_url(doc))


if __name__ == '__main__':
    unittest.main()
