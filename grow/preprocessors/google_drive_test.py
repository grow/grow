"""Tests for Google Drive preprocessor."""

import cStringIO
import copy
import csv
import json
import unittest
import mock
import yaml
from grow.pods import pods
from grow import storage
from grow.testing import google_service
from grow.testing import testing
from . import google_drive
from . import base


class GoogleSheetsPreprocessorTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    @staticmethod
    def _setup_mocks(sheets_get=None, sheets_values=None):
        if sheets_get is None:
            sheets_get = {
                'spreadsheetId': 76543,
            }
        if sheets_values is None:
            sheets_values = []

        mock_sheets_service = google_service.GoogleServiceMock.mock_sheets_service(
            get=sheets_get, values=sheets_values)

        return mock_sheets_service

    def test_column_to_letter(self):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        self.assertEqual('A', preprocessor.column_to_letter(1))
        self.assertEqual('Z', preprocessor.column_to_letter(26))
        self.assertEqual('AA', preprocessor.column_to_letter(27))
        self.assertEqual('AZ', preprocessor.column_to_letter(52))
        self.assertEqual('BA', preprocessor.column_to_letter(53))

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

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_export_path_list(self, mock_service_sheets):
        path = '/content/pages/sheet.yaml'
        config = google_drive.GoogleSheetsPreprocessor.Config(
            id='A1B2C3D4E5F6', format='list', gid=765, path=path)
        preprocessor = google_drive.GoogleSheetsPreprocessor(self.pod, config)
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 4,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'name', 'age', '_comment'],
                ['1', 'Jim', 27, 'commenting'],
                ['2', 'Sue', 23, 'something'],
            ],
        })
        mock_service_sheets.return_value = mock_sheets_service['service']
        preprocessor.execute(config)
        formatted_data = [{'age': 27, 'id': '1', 'name': 'Jim'},
                          {'age': 23, 'id': '2', 'name': 'Sue'}]
        result = self.pod.read_yaml(path)
        self.assertEqual(formatted_data, result)

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_export_collection_string(self, mock_service_sheets):
        config = google_drive.GoogleSheetsPreprocessor.Config(
            id='A1B2C3D4E5F6', format='string', collection='/content/pages/')
        preprocessor = google_drive.GoogleSheetsPreprocessor(self.pod, config)
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 2,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'name'],
                ['key', 'value'],
                ['other_key', 'foo'],
            ],
        })
        mock_service_sheets.return_value = mock_sheets_service['service']
        preprocessor.execute(config)
        formatted_data = {
            'key': 'value',
            'other_key': 'foo',
        }
        result = self.pod.read_yaml('/content/pages/sheet1.yaml')
        self.assertEqual(formatted_data, result)

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_download_list(self, mock_service_sheets):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 4,
                        'rowCount': 1000
                    },
                },
            }, {
                'properties': {
                    'title': 'sheet2',
                    'sheetId': 193,
                    'gridProperties': {
                        'columnCount': 2,
                        'rowCount': 1000
                    },
                },
            }, {
                'properties': {
                    'title': '_sheet3',
                    'sheetId': 922,
                    'gridProperties': {
                        'columnCount': 2,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'name', 'age', '_comment'],
                ['1', 'Jim', 27, 'commenting'],
                ['2', 'Sue', 23, 'something'],
            ],
        })
        mock_service_sheets.return_value = mock_sheets_service['service']
        gid_to_sheet, gid_to_data = preprocessor.download('A1B2C3D4E5F6')

        self.assertEqual({
            765: {
                'title': 'sheet1',
                'sheetId': 765,
                'gridProperties': {
                    'columnCount': 4,
                    'rowCount': 1000
                },
            },
            193: {
                'title': 'sheet2',
                'sheetId': 193,
                'gridProperties': {
                    'columnCount': 2,
                    'rowCount': 1000
                },
            },
            922: {
                'title': '_sheet3',
                'sheetId': 922,
                'gridProperties': {
                    'columnCount': 2,
                    'rowCount': 1000
                },
            }
        }, gid_to_sheet)

        self.assertEqual({
            193: [{'age': 27, 'id': '1', 'name': 'Jim'},
                  {'age': 23, 'id': '2', 'name': 'Sue'}],
            765: [{'age': 27, 'id': '1', 'name': 'Jim'},
                  {'age': 23, 'id': '2', 'name': 'Sue'}],
            922: [],
        }, gid_to_data)

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_download_map(self, mock_service_sheets):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 2,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'value'],
                ['jimbo', 'Jim'],
                ['suzette', 'Sue'],
            ],
        })
        mock_service_sheets.return_value = mock_sheets_service['service']
        gid_to_sheet, gid_to_data = preprocessor.download(
            'A1B2C3D4E5F6', format_as='map')

        self.assertEqual({
            765: {
                'title': 'sheet1',
                'sheetId': 765,
                'gridProperties': {
                    'columnCount': 2,
                    'rowCount': 1000
                },
            },
        }, gid_to_sheet)

        self.assertEqual({
            765: {
                'jimbo': 'Jim',
                'suzette': 'Sue',
            }
        }, gid_to_data)

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_download_grid(self, mock_service_sheets):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 3,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'key1', 'key2'],
                ['abc', 'a1', 'a2'],
                ['def', 'b1', 'b2'],
            ],
        })

        mock_service_sheets.return_value = mock_sheets_service['service']
        gid_to_sheet, gid_to_data = preprocessor.download(
            'A1B2C3D4E5F6', format_as='grid')

        self.assertEqual({
            765: {
                'title': 'sheet1',
                'sheetId': 765,
                'gridProperties': {
                    'columnCount': 3,
                    'rowCount': 1000,
                },
            },
        }, gid_to_sheet)

        self.assertEqual({
            765: {
                'abc': {
                    'key1': 'a1',
                    'key2': 'a2',
                },
                'def': {
                    'key1': 'b1',
                    'key2': 'b2',
                },
            },
        }, gid_to_data)

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_download_grid_duplicate(self, mock_service_sheets):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 3,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'key1', 'key2'],
                ['abc', 'a1', 'a2'],
                ['def', 'b1', 'b2'],
                ['abc', 'c1', 'c2'],
            ],
        })

        mock_service_sheets.return_value = mock_sheets_service['service']
        with self.assertRaises(base.PreprocessorError):
            preprocessor.download('A1B2C3D4E5F6', format_as='grid')

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_download_strings(self, mock_service_sheets):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 2,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'value'],
                ['jimbo', 'Jim'],
                ['suzette@', 'Sue'],
            ],
        })
        mock_service_sheets.return_value = mock_sheets_service['service']
        gid_to_sheet, gid_to_data = preprocessor.download(
            'A1B2C3D4E5F6', format_as='strings')

        self.assertEqual({
            765: {
                'title': 'sheet1',
                'sheetId': 765,
                'gridProperties': {
                    'columnCount': 2,
                    'rowCount': 1000
                },
            },
        }, gid_to_sheet)

        self.assertEqual({
            765: {
                'jimbo@': 'Jim',
                'suzette@': 'Sue',
            }
        }, gid_to_data)

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_download_strings_generate(self, mock_service_sheets):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 2,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={
            'values': [
                ['id', 'value'],
                ['jimbo', 'Jim'],
                ['suzette@', 'Sue'],
                ['', 'Lauren'],
                ['', 'Franz'],
            ],
        })
        mock_service_sheets.return_value = mock_sheets_service['service']
        gid_to_sheet, gid_to_data = preprocessor.download(
            'A1B2C3D4E5F6', format_as='strings', generate_ids=True)

        self.assertEqual({
            765: {
                'title': 'sheet1',
                'sheetId': 765,
                'gridProperties': {
                    'columnCount': 2,
                    'rowCount': 1000
                },
            },
        }, gid_to_sheet)

        self.assertEqual({
            765: {
                'jimbo@': 'Jim',
                'suzette@': 'Sue',
                'untranslated_0@': 'Lauren',
                'untranslated_1@': 'Franz',
            }
        }, gid_to_data)

    @mock.patch.object(google_drive.BaseGooglePreprocessor, 'create_service')
    def test_sheets_download_empty(self, mock_service_sheets):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        mock_sheets_service = self._setup_mocks(sheets_get={
            'spreadsheetId': 'A1B2C3D4E5F6',
            'sheets': [{
                'properties': {
                    'title': 'sheet1',
                    'sheetId': 765,
                    'gridProperties': {
                        'columnCount': 2,
                        'rowCount': 1000
                    },
                },
            }]
        }, sheets_values={})
        mock_service_sheets.return_value = mock_sheets_service['service']
        gid_to_sheet, gid_to_data = preprocessor.download('A1B2C3D4E5F6')

        self.assertEqual({
            765: {
                'title': 'sheet1',
                'sheetId': 765,
                'gridProperties': {
                    'columnCount': 2,
                    'rowCount': 1000
                },
            },
        }, gid_to_sheet)

        self.assertEqual({
            765: []
        }, gid_to_data)

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
        serialized_result = google_drive.GoogleSheetsPreprocessor.serialize_content(
            formatted_data=result, path=path)
        expected = yaml.safe_dump(content_dict, default_flow_style=False)
        self.assertEqual(expected, serialized_result)

        # Verify key_to_update.
        path = '/content/pages/test.yaml'
        existing_data = copy.deepcopy(content_dict)
        result = google_drive.GoogleSheetsPreprocessor.format_content(
            content=content, path=path, existing_data=existing_data,
            format_as='map', key_to_update='address')
        serialized_result = google_drive.GoogleSheetsPreprocessor.serialize_content(
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

        serialized_result = google_drive.GoogleSheetsPreprocessor.serialize_content(
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

    def test_parse_path(self):
        preprocessor = google_drive.GoogleSheetsPreprocessor
        self.assertEqual(('/path/a.yaml', None),
                         preprocessor.parse_path('/path/a.yaml'))
        self.assertEqual(['/path/a.yaml', 'b'],
                         preprocessor.parse_path('/path/a.yaml:b'))


if __name__ == '__main__':
    unittest.main()
