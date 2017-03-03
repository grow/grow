from . import base
from babel.messages import catalog
from babel.messages import pofile
from googleapiclient import discovery
from googleapiclient import errors
from googleapiclient import http
from grow.common import oauth
from grow.common import utils
from grow.preprocessors import google_drive
from grow.translators import errors as translator_errors
import base64
import csv
import datetime
import httplib2
import json
import logging
import random
import urllib
try:
    import cStringIO as StringIO
except ImportError:
    try:
        import StringIO
    except ImportError:
        from io import StringIO


class AccessLevel(object):
    COMMENTER = 'commenter'
    OWNER = 'owner'
    READER = 'reader'
    WRITER = 'writer'


DEFAULT_ACCESS_LEVEL = AccessLevel.WRITER


class GoogleSheetsTranslator(base.Translator):
    COLOR_GREY_200 = {
        'red': .933,
        'blue': .933,
        'green': .933,
    }
    COLOR_GREY_500 = {
        'red': .6196,
        'blue': .6196,
        'green': .6196,
    }
    KIND = 'google_sheets'
    HEADER_ROW_COUNT = 1
    # Source locale, translation locale, message location.
    HEADER_LABELS = [None, None, 'Location']
    has_immutable_translation_resources = False
    has_multiple_langs_in_one_resource = True

    def _create_service(self):
        return google_drive.BaseGooglePreprocessor.create_service(
                'sheets', 'v4')

    def _download_sheet(self, spreadsheet_id, locale):
        service = self._create_service()
        rangeName = "'{}'!A:C".format(locale)
        try:
            resp = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=rangeName).execute()
        except errors.HttpError as e:
            if e.resp['status'] == '400':
                raise translator_errors.NotFoundError(
                    'Translation for {} not found.'.format(locale))
            raise

        # Check for spreadsheets that are missing columns.
        column_count = len(self.HEADER_LABELS)
        if len(resp['values'][0]) < column_count:
            missing_columns = [None] * (column_count - len(resp['values'][0]))
            resp['values'][:] = [i + missing_columns for i in resp['values']]

        return resp['values']

    def _download_content(self, stat):
        spreadsheet_id = stat.ident
        values = self._download_sheet(spreadsheet_id, stat.lang)
        source_lang, lang, _ = values.pop(0)
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

    def _upload_catalogs(self, catalogs, source_lang, prune=False):
        project_title = self.project_title
        source_lang = str(source_lang)
        locales_to_sheet_ids = {}

        # Get existing sheet ID (if it exists) from one stat.
        spreadsheet_id = None
        stats_to_download = self._get_stats_to_download([])
        if stats_to_download:
            stat = stats_to_download.values()[0]
            spreadsheet_id = stat.ident if stat else None

        # NOTE: Manging locales across multiple spreadsheets is unsupported.
        service = self._create_service()
        if spreadsheet_id:
            resp = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id).execute()
            for sheet in resp['sheets']:
                locales_to_sheet_ids[sheet['properties']['title']] = \
                    sheet['properties']['sheetId']
            catalogs_to_create = []
            sheet_ids_to_catalogs = {}
            for catalog in catalogs:
                existing_sheet_id = locales_to_sheet_ids.get(str(catalog.locale))
                if existing_sheet_id:
                    sheet_ids_to_catalogs[existing_sheet_id] = catalog
                else:
                    catalogs_to_create.append(catalog)

            requests = []

            if catalogs_to_create:
                requests += self._generate_create_sheets_requests(
                    catalogs_to_create, source_lang)

            if sheet_ids_to_catalogs:
                requests += self._generate_update_sheets_requests(
                    sheet_ids_to_catalogs, source_lang, spreadsheet_id,
                            prune=prune)

            self._perform_batch_update(spreadsheet_id, requests)
        else:
            # Create a new spreadsheet and use the id.
            service = self._create_service()
            resp = service.spreadsheets().create(body={
                'properties': {
                    'title': project_title,
                },
            }).execute()
            spreadsheet_id = resp['spreadsheetId']

            requests = []
            requests += self._generate_create_sheets_requests(
                catalogs, source_lang)
            self._perform_batch_update(spreadsheet_id, requests)

            if 'acl' in self.config:
                self._do_update_acl(spreadsheet_id, self.config['acl'])

        stats = []
        for catalog in catalogs:
            url = 'https://docs.google.com/spreadsheets/d/{}'.format(spreadsheet_id)
            lang = str(catalog.locale)
            if lang in locales_to_sheet_ids:
                url += '#gid={}'.format(locales_to_sheet_ids[lang])
            stat = base.TranslatorStat(
                url=url,
                lang=lang,
                source_lang=source_lang,
                uploaded = datetime.datetime.now(),
                ident=spreadsheet_id)
            stats.append(stat)
        return stats

    def _create_header_row_data(self, source_lang, lang):
        return {
            'values': [
                {'userEnteredValue': {'stringValue': source_lang}},
                {'userEnteredValue': {'stringValue': lang}},
                {'userEnteredValue': {'stringValue': self.HEADER_LABELS[2]}},
            ]
        }

    def _create_catalog_row(self, id, value, locations):
        return {
            'values': [
                {'userEnteredValue': {'stringValue': id}},
                {'userEnteredValue': {'stringValue': value}},
                {'userEnteredValue': {
                        'stringValue': (', '.join(t[0] for t in locations))}},
            ],
        }

    def _create_catalog_rows(self, catalog, prune=False):
        rows = []
        for message in catalog:
            if not message.id:
                continue

            if prune and not message.locations:
                continue

            rows.append(self._create_catalog_row(
                    message.id, message.string, message.locations))
        return rows

    def _diff_data(self, existing_values, catalog):
        existing_rows = []
        new_rows = []
        removed_rows = []

        for value in existing_values:
            existing_rows.append({
                'source': value[0],
                'translation': value[1] if len(value) > 1 else None,
                'locations': value[2] if len(value) > 2 else [],
                'updated': False, # Has changed from the downloaded value.
                'matched': False, # Has been matched to the downloaded values.
            })

        for message in catalog:
            if not message.id:
                continue

            found = False

            # Update for any existing values.
            for value in existing_rows:
                if value['source'] == message.id:
                    value['updated'] = (
                            value['translation'] != message.string or
                            value['locations'] != message.locations)
                    value['translation'] = message.string
                    value['locations'] = message.locations
                    value['matched'] = True
                    found = True
                    break

            if found == True:
                continue

            new_rows.append({
                'source': message.id,
                'translation': message.string,
                'locations': message.locations,
            })

        for index, value in enumerate(existing_rows):
            if not value['matched'] or len(value['locations']) == 0:
                removed_rows.append(index)

            # Reset the locations when not found in catalog.
            if not value['matched']:
                value['locations'] = []

        return (existing_rows, new_rows, removed_rows)

    def _generate_create_sheets_requests(self, catalogs, source_lang):
        # Create sheets.
        requests = []
        for catalog in catalogs:
            sheet_id = random.randrange(100, 9999999)
            lang = str(catalog.locale)
            # Create a new sheet.
            requests.append({
                'addSheet': {
                    'properties': {
                        'sheetId': sheet_id,
                        'title': lang,
                        'gridProperties': {
                            'columnCount': 3,
                            'rowCount': self.HEADER_ROW_COUNT + 1,
                            'frozenRowCount': 1,
                            'frozenColumnCount': 1,
                        },
                    },
                },
            })

            # Add the data to the new sheet.
            _, new_rows, _ = self._diff_data([], catalog)
            row_data = []
            row_data.append(self._create_header_row_data(source_lang, lang))

            if len(new_rows):
                for value in new_rows:
                    row_data.append(self._create_catalog_row(
                            value['source'], value['translation'],
                            value['locations']))

                requests.append({
                    'appendCells': {
                        'sheetId': sheet_id,
                        'fields': 'userEnteredValue',
                        'rows': row_data,
                    },
                })

            # Format the new sheet.
            requests += self._generate_style_requests(sheet_id)

            # Size the initial sheet columns.
            # Not part of the style request to respect user's choice to resize.
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 2,
                    },
                    'properties': {
                        'pixelSize': 400, # Source and Translation Columns
                    },
                    'fields': '*',
                },
            })

            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 2,
                        'endIndex': 3,
                    },
                    'properties': {
                        'pixelSize': 200, # Location Column
                    },
                    'fields': '*',
                },
            })

        return requests

    def _generate_style_requests(self, sheet_id):
        formats = {}

        formats['header_cell'] = {
            'backgroundColor': self.COLOR_GREY_200,
            'textFormat': {
                'bold': True
            },
        }

        formats['info_cell'] = {
            'wrapStrategy': 'WRAP',
            'textFormat': {
                'foregroundColor': self.COLOR_GREY_500,
            },
        }

        formats['wrap'] = {'wrapStrategy': 'WRAP'}

        requests = []
        requests.append({
            'repeatCell': {
                'fields': 'userEnteredFormat',
                'range': {
                    'sheetId': sheet_id,
                    'startColumnIndex': 0,
                    'startRowIndex': 0,
                    'endRowIndex': self.HEADER_ROW_COUNT,
                },
                'cell': {
                    'userEnteredFormat': formats['header_cell'],
                },
            },
        })
        requests.append({
            'repeatCell': {
                'fields': 'userEnteredFormat',
                'range': {
                    'sheetId': sheet_id,
                    'startColumnIndex': 0,
                    'endColumnIndex': 2,
                    'startRowIndex': self.HEADER_ROW_COUNT,
                },
                'cell': {
                    'userEnteredFormat': formats['wrap'],
                },
            },
        })
        requests.append({
            'repeatCell': {
                'fields': 'userEnteredFormat',
                'range': {
                    'sheetId': sheet_id,
                    'startColumnIndex': 2,
                    'endColumnIndex': 3,
                    'startRowIndex': self.HEADER_ROW_COUNT,
                },
                'cell': {
                    'userEnteredFormat': formats['info_cell'],
                },
            },
        })
        return requests

    def _generate_update_sheets_requests(self, sheet_ids_to_catalogs,
            source_lang, spreadsheet_id, prune=False):
        requests = []
        for sheet_id, catalog in sheet_ids_to_catalogs.iteritems():
            lang = str(catalog.locale)
            existing_values = self._download_sheet(spreadsheet_id, lang)
            for x in range(self.HEADER_ROW_COUNT):
                existing_values.pop(0)  # Remove header rows.
            for value in existing_values:
                if value not in catalog:
                    source = value[0]
                    translation = value[1] if len(value) > 1 else None
                    catalog.add(source, translation, auto_comments=[],
                                context=None, flags=[])

            # Check for missing columns.
            num_missing_columns = 0
            for column in existing_values[0]:
                if column == None:
                    num_missing_columns += 1
            if num_missing_columns:
                requests.append({
                    'appendDimension': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'length': num_missing_columns,
                    },
                })

                # Update the column headers.
                requests.append({
                    'updateCells': {
                        'fields': 'userEnteredValue',
                        'start': {
                            'sheetId': sheet_id,
                            'rowIndex': 0,
                            'columnIndex': 0,
                        },
                        'rows': [
                            self._create_header_row_data(source_lang, lang)
                        ],
                    },
                })

            # Perform a diff of the existing data to what the catalog provides
            # to make targeted changes to the spreadsheet and preserve meta
            # information--such as comments.
            existing_rows, new_rows, removed_rows = self._diff_data(
                    existing_values, catalog)

            # Update the existing values in place.
            if len(existing_rows):
                row_data = []
                for value in existing_rows:
                    row_data.append(self._create_catalog_row(
                            value['source'], value['translation'],
                            value['locations']))
                # NOTE This is not (yet) smart enough to only update small sections
                # with the updated information. Hint: Use value['updated'].
                requests.append({
                    'updateCells': {
                        'fields': 'userEnteredValue',
                        'start': {
                            'sheetId': sheet_id,
                            'rowIndex': self.HEADER_ROW_COUNT, # Skip header row.
                            'columnIndex': 0,
                        },
                        'rows': row_data,
                    },
                })

            # Append new values to end of sheet.
            if len(new_rows):
                row_data = []
                for value in new_rows:
                    row_data.append(self._create_catalog_row(
                            value['source'], value['translation'],
                            value['locations']))

                requests.append({
                    'appendCells': {
                        'sheetId': sheet_id,
                        'fields': 'userEnteredValue',
                        'rows': row_data,
                    },
                })

            # Remove obsolete rows if not included.
            if prune and len(removed_rows):
                for value in reversed(removed_rows): # Start from the bottom.
                    # NOTE this is ineffecient since it does not combine ranges.
                    # ex: 1, 2, 3 are three requests instead of one request 1-3
                    requests.append({
                        'deleteDimension': {
                            'range': {
                                'sheetId': sheet_id,
                                'dimension': 'ROWS',
                                'startIndex': self.HEADER_ROW_COUNT + value,
                                'endIndex': self.HEADER_ROW_COUNT + value + 1,
                            },
                        },
                    })

            # Sort all rows.
            requests.append({
                'sortRange': {
                    'range': {
                        'sheetId': sheet_id,
                        'startColumnIndex': 0,
                        'startRowIndex': self.HEADER_ROW_COUNT,
                    },
                    'sortSpecs': [
                        {
                            'dimensionIndex': 0,
                            'sortOrder': 'ASCENDING',
                        }
                    ],
                },
            })
        return requests

    def _do_update_acl(self, spreadsheet_id, acl):
        service = google_drive.BaseGooglePreprocessor.create_service('drive', 'v3')
        for item in acl:
            permission = {
                'role': item.get('role', DEFAULT_ACCESS_LEVEL).lower(),
            }
            if 'domain' in item:
                permission['type'] = 'domain'
                permission['domain'] = item['domain']
            elif 'user' in item:
                permission['type'] = 'user'
                permission['emailAddress'] = item['user']
            elif 'group' in item:
                permission['type'] = 'group'
                permission['emailAddress'] = item['group']
            resp = service.permissions().create(
                fileId=spreadsheet_id,
                body=permission).execute()

    def _perform_batch_update(self, spreadsheet_id, requests):
        service = self._create_service()
        body = {'requests': requests}
        return service.spreadsheets().batchUpdate(
            spreadsheetId=spreadsheet_id, body=body).execute()

    def _update_acls(self, stats, locales):
        if 'acl' not in self.config:
            return
        stat = stats.values()[0]
        spreadsheet_id = stat.ident
        acl = self.config['acl']
        if not acl:
            return
        self._do_update_acl(spreadsheet_id, acl)

    def _update_meta(self, stat, locale):
        spreadsheet_id = stat.ident
        locales_to_sheet_ids = {}
        service = self._create_service()
        resp = service.spreadsheets().get(
            spreadsheetId=stat.ident).execute()
        requests = []
        for sheet in resp['sheets']:
            sheet_id = sheet['properties']['sheetId']
            requests += self._generate_style_requests(sheet_id)
        self._perform_batch_update(spreadsheet_id, requests)
