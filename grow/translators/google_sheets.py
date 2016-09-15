import csv
from . import base
from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient import http
from babel.messages import pofile
from babel.messages import catalog
from grow.common import oauth
from grow.common import utils
from grow.preprocessors import google_drive
import datetime
import base64
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


def raise_service_error(http_error, ident=None):
    message = 'HttpError {} for {} returned "{}"'.format(
        http_error.resp.status, http_error.uri,
        http_error._get_reason().strip())
    raise base.TranslatorServiceError(message=message, ident=ident)


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
        rangeName = 'A:B'  # First two columns (source:translation).
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

    def _upload_catalogs(self, catalog, source_lang):
        project_title = self.project_title
        source_lang = str(source_lang)
        service = self._create_service()
        range_name = 'Sheet1!A:B'
        major_dimension = 'columns'
        lang = str(catalog.locale)
        stats_to_download = self._get_stats_to_download([lang])
        stat = stats_to_download.get(lang)
        sheet_id = stat.ident if stat else None
        if sheet_id:
            resp = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        else:
            row_data = []
            row_data.append({
                'values': [
                    {'userEnteredValue': {'stringValue': source_lang},
                     'userEnteredFormat': {
                         'backgroundColor': {'red': 100, 'blue': 100, 'green': 100, 'alpha': .1},
                         'textFormat': {'bold': True},
                     }},
                    {'userEnteredValue': {'stringValue': lang},
                     'userEnteredFormat': {
                         'backgroundColor': {'red': 100, 'blue': 100, 'green': 100, 'alpha': .1},
                         'textFormat': {'bold': True},
                     },
                    },
                ]
            })
            for message in catalog:
                if not message.id:
                    continue
                row_data.append({
                    'values': [
                        {'userEnteredValue': {'stringValue': message.id},
                         'userEnteredFormat': {'wrapStrategy': 'WRAP'}},
                        {'userEnteredValue': {'stringValue': message.string},
                         'userEnteredFormat': {'wrapStrategy': 'WRAP'}},
                    ],
                })
            sheets = []
            sheet = {
                'properties': {
                    'title': lang,
                    'gridProperties': {
                        'columnCount': 2,
                        'frozenRowCount': 1,
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
            sheets.append(sheet)
            resp = service.spreadsheets().create(body={
                'properties': {
                    'title': project_title,
                },
                'sheets': sheets,
            }).execute()
        ident = resp['spreadsheetId']
        url = 'https://docs.google.com/spreadsheets/d/{}'.format(ident)
        return base.TranslatorStat(
            url=url,
            lang=lang,
            source_lang=source_lang,
            uploaded = datetime.datetime.now(),
            ident=ident)
