from . import base
from babel.messages import catalog
from babel.messages import pofile
from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient import http
from grow.common import oauth
from grow.common import utils
from grow.preprocessors import google_drive
import base64
import csv
import datetime
import httplib2
import json
import logging
import urllib
try:
    import cStringIO as StringIO
except ImportError:
    try:
        import StringIO
    except ImportError:
        from io import StringIO


class AccessLevel(object):
    ADMIN = 'ADMIN'
    READ_AND_COMMENT = 'READ_AND_COMMENT'
    READ_AND_WRITE = 'READ_AND_WRITE'
    READ_ONLY = 'READ_ONLY'


class GoogleSheetsTranslator(base.Translator):
    KIND = 'google_sheets'
    has_immutable_translation_resources = False
    has_multiple_langs_in_one_resource = True

    def _create_service(self):
        return google_drive.BaseGooglePreprocessor.create_service('sheets', 'v4')

    def _download_content(self, stat):
        sheet_id = stat.ident
        gid = None
        service = self._create_service()
        # First two columns (source:translation).
        rangeName = "'{}'!A:B".format(stat.lang)
        resp = service.spreadsheets().values().get(
            spreadsheetId=sheet_id, range=rangeName).execute()
        values = resp['values']
        source_lang, lang = values.pop(0)
        babel_catalog = catalog.Catalog(stat.lang)
        for row in values:
            source = row[0]
            translation = row[1] if len(row) > 1 else None
            babel_catalog.add(source, translation, auto_comments=[],
                              context=None, flags=[])
        updated_stat = base.TranslatorStat(
            url=stat.url,
            lang=stat.lang,
            downloaded = datetime.datetime.now(),
            source_lang=stat.source_lang,
            ident=stat.ident)
        fp = StringIO.StringIO()
        pofile.write_po(fp, babel_catalog)
        fp.seek(0)
        content = fp.read()
        return updated_stat, content

    def _upload_catalogs(self, catalogs, source_lang):
        project_title = self.project_title
        source_lang = str(source_lang)

        # Get existing sheet ID (if it exists) from one stat.
        stats_to_download = self._get_stats_to_download([])
        if stats_to_download:
            stat = stats_to_download.values()[0]
            sheet_id = stat.ident if stat else None
        else:
            sheet_id = None

        service = self._create_service()
        if sheet_id:
            resp = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        else:
            sheets = []
            for catalog in catalogs:
                sheets.append(self._create_sheet_from_catalog(catalog, source_lang))
            resp = service.spreadsheets().create(body={
                'sheets': sheets,
                'properties': {
                    'title': project_title,
                },
            }).execute()
        ident = resp['spreadsheetId']
        url = 'https://docs.google.com/spreadsheets/d/{}'.format(ident)
        stats = []
        for catalog in catalogs:
            stat = base.TranslatorStat(
                url=url,
                lang=str(catalog.locale),
                source_lang=source_lang,
                uploaded = datetime.datetime.now(),
                ident=ident)
            stats.append(stat)
        return stats

    def _create_header_row_data(self, source_lang, lang):
        return {
            'values': [
                {
                    'userEnteredValue': {'stringValue': source_lang},
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 50, 'blue': 50, 'green': 50, 'alpha': .1},
                        'textFormat': {'bold': True},
                    }
                },
                {
                    'userEnteredValue': {'stringValue': lang},
                    'userEnteredFormat': {
                        'backgroundColor': {'red': 50, 'blue': 50, 'green': 50, 'alpha': .1},
                        'textFormat': {'bold': True},
                    }
                },
            ]
        }

    def _create_catalog_rows(self, catalog):
        rows = []
        for message in catalog:
            if not message.id:
                continue
            rows.append({
                'values': [
                    {
                        'userEnteredValue': {'stringValue': message.id},
                        'userEnteredFormat': {'wrapStrategy': 'WRAP'}
                    },
                    {
                        'userEnteredValue': {'stringValue': message.string},
                        'userEnteredFormat': {'wrapStrategy': 'WRAP'}
                    },
                ],
            })
        return rows

    def _create_sheet_from_catalog(self, catalog, source_lang):
        lang = str(catalog.locale)
        row_data = []
        row_data.append(self._create_header_row_data(source_lang, lang))
        row_data += self._create_catalog_rows(catalog)
        return {
            'properties': {
                'title': lang,
                'gridProperties': {
                    'columnCount': 2,
                    'rowCount': len(row_data) + 3,  # Three rows of padding.
                    'frozenRowCount': 1,
                    'frozenColumnCount': 1,
                },
            },
            'data': [{
                'startRow': 0,
                'startColumn': 0,
                'rowData': row_data,
                'columnMetadata': [
                    {'pixelSize': 400},
                    {'pixelSize': 400},
                ],
            }],
        }
