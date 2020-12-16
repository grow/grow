"""Google Sheets for translating pod content."""

import datetime
import io
import progressbar
import random
from babel.messages import catalog
from babel.messages import pofile
from googleapiclient import errors
from grow.common import progressbar_non
from grow.preprocessors import google_drive
from grow.translators import errors as translator_errors
try:
    import io as StringIO
except ImportError:  # pragma: no cover
    try:
        import io
    except ImportError:
        from io import StringIO
from . import base


class AccessLevel(object):
    COMMENTER = 'commenter'
    OWNER = 'owner'
    READER = 'reader'
    WRITER = 'writer'


DEFAULT_ACCESS_LEVEL = AccessLevel.WRITER
OAUTH_SCOPE = 'https://www.googleapis.com/auth/spreadsheets'


class GoogleSheetsTranslator(base.Translator):
    COLOR_DEEP_PURPLE_50 = {
        'red': 0.929,
        'green': 0.905,
        'blue': 0.964,
    }
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
    HEADER_LABELS = [None, None, 'Extracted comments', 'Reference']
    SHEETS_BASE_URL = 'https://docs.google.com/spreadsheets/d/'
    has_immutable_translation_resources = False
    has_multiple_langs_in_one_resource = True

    def __init__(self, pod, config=None, project_title=None, instructions=None):
        super(GoogleSheetsTranslator, self).__init__(
            pod, config=config, project_title=project_title,
            instructions=instructions)
        self.update_meta_after_upload = False

    def needs_meta_update(self):
        """Allow to be flagged for additional meta update after uploading."""
        return self.update_meta_after_upload

    def _catalog_has_comments(self, catalog):
        for message in catalog:
            if not message.id:
                continue

            if message.auto_comments:
                return True
        return False

    def _content_hash(self, location, locale):
        return hash((location, locale)) % (10 ** 8)  # 10 Digits of the hash.

    def _create_service(self):  # pragma: no cover
        return google_drive.BaseGooglePreprocessor.create_service(
            'sheets', 'v4')

    def _download_sheet(self, spreadsheet_id, locale):
        service = self._create_service()
        rangeName = "'{}'!A:D".format(locale)
        try:
            # pylint: disable=no-member
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

    def _download_sheets(self, spreadsheet_id, locales):
        service = self._create_service()

        # Find out which locales have sheets.
        # pylint: disable=no-member
        resp = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id).execute()
        existing_locales = []
        for sheet in resp['sheets']:
            existing_locales.append(sheet['properties']['title'])

        rangeNames = []
        rangeLocales = []
        skipped_locales = []
        for locale in locales:
            # Skip locales that do not have sheets.
            if locale not in existing_locales:
                skipped_locales.append(locale)
                continue

            rangeLocales.append(locale)
            rangeNames.append("'{}'!A:D".format(locale))

        if skipped_locales:
            self.pod.logger.info(
                'Skipping locales, missing sheet: {}'.format(', '.join(skipped_locales)))

        try:
            # pylint: disable=no-member
            batch_resp = service.spreadsheets().values().batchGet(
                spreadsheetId=spreadsheet_id, ranges=rangeNames).execute()

            locale_to_values = {}
            for i, locale in enumerate(rangeLocales):
                resp = batch_resp['valueRanges'][i]

                # Check for spreadsheets that are missing columns.
                column_count = len(self.HEADER_LABELS)
                if len(resp['values'][0]) < column_count:
                    missing_columns = [None] * (column_count - len(resp['values'][0]))
                    resp['values'][:] = [i + missing_columns for i in resp['values']]
                locale_to_values[locale] = resp['values']

            return locale_to_values
        except errors.HttpError as e:
            if e.resp['status'] == '400':
                raise translator_errors.NotFoundError(
                    'Translation for {} not found.'.format(locales))
            raise

    def _download_content(self, stat, values):
        # Ignore the header row.
        values.pop(0)
        babel_catalog = catalog.Catalog(stat.lang)
        for row in values:
            # Skip empty rows.
            if not row or self._is_empty_row(row):
                continue
            source = row[0]
            translation = row[1] if len(row) > 1 else None
            babel_catalog.add(source, translation, auto_comments=[],
                              context=None, flags=[])
        updated_stat = base.TranslatorStat(
            url=stat.url,
            lang=stat.lang,
            downloaded=datetime.datetime.now(),
            source_lang=stat.source_lang,
            ident=stat.ident)
        fp = io.BytesIO()
        pofile.write_po(fp, babel_catalog)
        fp.seek(0)
        content = fp.read()
        return updated_stat, content

    def _is_empty_row(self, row):
        return bool(set(row) - set((None, ''))) is False

    def _upload_catalogs(self, catalogs, source_lang, prune=False):
        if not catalogs:
            raise translator_errors.NoCatalogsError('Missing catalogs to upload.')

        project_title = self.project_title
        source_lang = str(source_lang)
        locales_to_sheet_ids = {}

        # Get existing sheet ID (if it exists) from one stat.
        spreadsheet_id = None
        stats_to_download = self._get_stats_to_download([])
        if stats_to_download:
            stat = list(stats_to_download.values())[0]
            spreadsheet_id = stat.ident if stat else None

        # NOTE: Manging locales across multiple spreadsheets is unsupported.
        service = self._create_service()
        if spreadsheet_id:
            # pylint: disable=no-member
            resp = service.spreadsheets().get(
                spreadsheetId=spreadsheet_id).execute()
            for sheet in resp['sheets']:
                locales_to_sheet_ids[sheet['properties']['title']] = \
                    sheet['properties']['sheetId']
            catalogs_to_create = []
            sheet_ids_to_catalogs = {}

            for catalog in catalogs:
                existing_sheet_id = locales_to_sheet_ids.get(
                    str(catalog.locale))
                if existing_sheet_id:
                    sheet_ids_to_catalogs[existing_sheet_id] = catalog
                elif source_lang != str(catalog.locale):
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
            # pylint: disable=no-member
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
            if str(catalog.locale) == source_lang:
                continue
            url = '{}{}'.format(self.SHEETS_BASE_URL, spreadsheet_id)
            lang = str(catalog.locale)
            if lang in locales_to_sheet_ids:
                url += '#gid={}'.format(locales_to_sheet_ids[lang])
            stat = base.TranslatorStat(
                url=url,
                lang=lang,
                source_lang=source_lang,
                uploaded=datetime.datetime.now(),
                ident=spreadsheet_id)
            stats.append(stat)
        return stats

    def _create_header_row_data(self, source_lang, lang):
        return {
            'values': [
                {'userEnteredValue': {'stringValue': source_lang}},
                {'userEnteredValue': {'stringValue': lang}},
                {'userEnteredValue': {'stringValue': self.HEADER_LABELS[2]}},
                {'userEnteredValue': {'stringValue': self.HEADER_LABELS[3]}},
            ]
        }

    def _create_catalog_row(self, id, value, comments, locations):
        comments = [] if comments is None else comments
        return {
            'values': [
                {'userEnteredValue': {'stringValue': id}},
                {'userEnteredValue': {'stringValue': value}},
                {'userEnteredValue': {'stringValue': '\n'.join(comments)}},
                {'userEnteredValue': {
                    'stringValue': ', '.join(t[0] for t in locations)}},
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
                message.id, message.string, message.auto_comments, message.locations))
        return rows

    def _diff_data(self, existing_values, catalog):
        existing_rows = []
        new_rows = []
        removed_rows = []

        for value in existing_values:
            if not value or self._is_empty_row(value):  # Skip empty rows.
                continue
            existing_rows.append({
                'source': value[0],
                'translation': value[1] if len(value) > 1 else None,
                'comments': value[2] if len(value) > 2 else [],
                'locations': value[3] if len(value) > 3 else [],
                'updated': False,  # Has changed from the downloaded value.
                'matched': False,  # Has been matched to the downloaded values.
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
                    value['comments'] = message.auto_comments
                    value['matched'] = True
                    found = True
                    break

            if found == True:
                continue

            new_rows.append({
                'source': message.id,
                'translation': message.string,
                'locations': message.locations,
                'comments': message.auto_comments,
            })

        for index, value in enumerate(existing_rows):
            if not value['matched'] or len(value['locations']) == 0:
                removed_rows.append(index)

            # Reset the locations when not found in catalog.
            if not value['matched']:
                value['locations'] = []

        return (existing_rows, new_rows, removed_rows)

    def _generate_comments_column_requests(self, sheet_id, catalog):
        requests = []
        sheet_range = {
            'sheetId': sheet_id,
            'dimension': 'COLUMNS',
            'startIndex': 2,
            'endIndex': 3,
        }

        if self._catalog_has_comments(catalog):
            requests.append({
                'updateDimensionProperties': {
                    'range': sheet_range,
                    'properties': {
                        'hiddenByUser': False,
                    },
                    'fields': 'hiddenByUser',
                },
            })
        else:
            requests.append({
                'updateDimensionProperties': {
                    'range': sheet_range,
                    'properties': {
                        'hiddenByUser': True,
                    },
                    'fields': 'hiddenByUser',
                },
            })

        return requests

    def _generate_create_sheets_requests(self, catalogs, source_lang):
        # Create sheets.
        requests = []
        for catalog in catalogs:
            sheet_id = self._generate_new_sheet_id()
            lang = str(catalog.locale)
            # Create a new sheet.
            requests.append({
                'addSheet': {
                    'properties': {
                        'sheetId': sheet_id,
                        'title': lang,
                        'gridProperties': {
                            'columnCount': 4,
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
                        value['comments'], value['locations']))

                requests.append({
                    'appendCells': {
                        'sheetId': sheet_id,
                        'fields': 'userEnteredValue',
                        'rows': row_data,
                    },
                })

            # Format the new sheet.
            requests += self._generate_style_requests(
                sheet_id, catalog=catalog)

            # Size the initial sheet columns.
            # Not part of the style request to respect user's choice to resize.
            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 0,
                        'endIndex': 3,
                    },
                    'properties': {
                        'pixelSize': 400,  # Source and Translation Columns
                    },
                    'fields': 'pixelSize',
                },
            })

            requests.append({
                'updateDimensionProperties': {
                    'range': {
                        'sheetId': sheet_id,
                        'dimension': 'COLUMNS',
                        'startIndex': 3,
                        'endIndex': 4,
                    },
                    'properties': {
                        'pixelSize': 200,  # Location Column
                    },
                    'fields': 'pixelSize',
                },
            })

            requests += self._generate_comments_column_requests(
                sheet_id, catalog)

        return requests

    def _generate_filter_view_requests(self, sheet_id, sheet, filter_view):
        requests = []

        is_filtered = False
        if sheet and 'filterViews' in sheet:
            for existing_range in sheet['filterViews']:
                if existing_range['filterViewId'] == filter_view['filterViewId']:
                    is_filtered = True
                    requests.append({
                        'updateFilterView': {
                            'filter': filter_view,
                            'fields': 'range,title,criteria',
                        },
                    })
                    break

        if not is_filtered:
            requests.append({
                'addFilterView': {
                    'filter': filter_view,
                },
            })

        return requests

    def _generate_new_sheet_id(self):
        return random.randrange(100, 9999999)

    def _generate_style_requests(self, sheet_id, sheet=None, catalog=None):
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

        formats['missing_cell'] = {
            'backgroundColor': self.COLOR_DEEP_PURPLE_50,
        }

        formats['wrap'] = {'wrapStrategy': 'WRAP'}

        requests = []

        # TODO Figure out how to be smarter about matching conditional formatting.
        # Remove all existing conditional formatting. :(
        if sheet and 'conditionalFormats' in sheet:
            for _ in sheet['conditionalFormats']:
                requests.append({
                    'deleteConditionalFormatRule': {
                        'sheetId': sheet_id,
                        'index': 0
                    }
                })

        # Style header cells.
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

        # Allow the translations and comments to wrap.
        requests.append({
            'repeatCell': {
                'fields': 'userEnteredFormat',
                'range': {
                    'sheetId': sheet_id,
                    'startColumnIndex': 0,
                    'endColumnIndex': 3,
                    'startRowIndex': self.HEADER_ROW_COUNT,
                },
                'cell': {
                    'userEnteredFormat': formats['wrap'],
                },
            },
        })

        # Comment and source cells are muted in styling.
        requests.append({
            'repeatCell': {
                'fields': 'userEnteredFormat',
                'range': {
                    'sheetId': sheet_id,
                    'startColumnIndex': 2,
                    'endColumnIndex': 4,
                    'startRowIndex': self.HEADER_ROW_COUNT,
                },
                'cell': {
                    'userEnteredFormat': formats['info_cell'],
                },
            },
        })

        # Highlight missing translations.
        requests.append({
            'addConditionalFormatRule': {
                'rule': {
                    'ranges': [{
                        'sheetId': sheet_id,
                        'startColumnIndex': 1,
                        'endColumnIndex': 2,
                        'startRowIndex': self.HEADER_ROW_COUNT,
                    }],
                    'booleanRule': {
                        'condition': {'type': 'BLANK'},
                        'format': formats['missing_cell']
                    }
                },
                'index': 0
            }
        })

        # Protect the original values.
        requests += self._generate_style_protected_requests(sheet_id, sheet, {
            'protectedRangeId': sheet_id + 1000001,  # Keep it predictble.
            'range': {
                'sheetId': sheet_id,
                'startColumnIndex': 0,
                'endColumnIndex': 1,
                'startRowIndex': self.HEADER_ROW_COUNT,
            },
            'description': 'Original strings can only be edited in the source files.',
            'warningOnly': True,
        })

        # Protect the comment values.
        requests += self._generate_style_protected_requests(sheet_id, sheet, {
            'protectedRangeId': sheet_id + 1000002,  # Keep it predictble.
            'range': {
                'sheetId': sheet_id,
                'startColumnIndex': 2,
                'endColumnIndex': 3,
                'startRowIndex': self.HEADER_ROW_COUNT,
            },
            'description': 'Comment strings can only be edited in the source files.',
            'warningOnly': True,
        })

        # Protect the location values.
        requests += self._generate_style_protected_requests(sheet_id, sheet, {
            'protectedRangeId': sheet_id + 1000003,  # Keep it predictble.
            'range': {
                'sheetId': sheet_id,
                'startColumnIndex': 3,
                'endColumnIndex': 4,
                'startRowIndex': self.HEADER_ROW_COUNT,
            },
            'description': 'Source strings can only be edited in the source files.',
            'warningOnly': True,
        })

        # Filter view for untranslated strings.
        requests += self._generate_filter_view_requests(sheet_id, sheet, {
            'filterViewId': sheet_id + 3300001,  # Keep it predictble.
            'range': {
                'sheetId': sheet_id,
                'startColumnIndex': 0,
                'endColumnIndex': 4,
                'startRowIndex': 0,
            },
            'title': 'Untranslated Strings',
            'criteria': {
                '1': {
                    'condition': {'type': 'BLANK'}
                },
            },
        })

        return requests

    def _generate_style_protected_requests(self, sheet_id, sheet, protected_range):
        requests = []

        is_protected = False
        if sheet and 'protectedRanges' in sheet:
            for existing_range in sheet['protectedRanges']:
                if existing_range['protectedRangeId'] == protected_range['protectedRangeId']:
                    is_protected = True
                    requests.append({
                        'updateProtectedRange': {
                            'protectedRange': protected_range,
                            'fields': 'range,description,warningOnly',
                        },
                    })
                    break

        if not is_protected:
            requests.append({
                'addProtectedRange': {
                    'protectedRange': protected_range,
                },
            })

        return requests

    def _generate_update_sheets_requests(self, sheet_ids_to_catalogs,
                                         source_lang, spreadsheet_id, prune=False):
        requests = []
        for sheet_id, catalog in sheet_ids_to_catalogs.items():
            lang = str(catalog.locale)
            existing_values = self._download_sheet(spreadsheet_id, lang)
            for x in range(self.HEADER_ROW_COUNT):
                existing_values.pop(0)  # Remove header rows.
            for value in existing_values:
                if not value or self._is_empty_row(value):  # Skip empty rows.
                    continue
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
                    if not value:  # Skip empty rows.
                        continue
                    row_data.append(self._create_catalog_row(
                        value['source'], value['translation'],
                        value['comments'], value['locations']))
                # NOTE This is not (yet) smart enough to only update small sections
                # with the updated information. Hint: Use value['updated'].
                requests.append({
                    'updateCells': {
                        'fields': 'userEnteredValue',
                        'start': {
                            'sheetId': sheet_id,
                            # Skip header row.
                            'rowIndex': self.HEADER_ROW_COUNT,
                            'columnIndex': 0,
                        },
                        'rows': row_data,
                    },
                })

            # Append new values to end of sheet.
            if len(new_rows):
                # Mark to update the sheet metadata after done.
                self.update_meta_after_upload = True
                row_data = []
                for value in new_rows:
                    row_data.append(self._create_catalog_row(
                        value['source'], value['translation'],
                        value['comments'], value['locations']))

                requests.append({
                    'appendCells': {
                        'sheetId': sheet_id,
                        'fields': 'userEnteredValue',
                        'rows': row_data,
                    },
                })

            # Remove obsolete rows if not included.
            if prune and len(removed_rows):
                for value in reversed(removed_rows):  # Start from the bottom.
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

            requests += self._generate_comments_column_requests(
                sheet_id, catalog)
        return requests

    def _do_update_acl(self, spreadsheet_id, acl):
        service = google_drive.BaseGooglePreprocessor.create_service(
            'drive', 'v3')
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
            # pylint: disable=no-member
            resp = service.permissions().create(
                fileId=spreadsheet_id,
                body=permission).execute()

    def _perform_batch_update(self, spreadsheet_id, requests):
        service = self._create_service()
        body = {'requests': requests}
        # pylint: disable=no-member
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

    def _update_meta(self, stat, locale, catalog):
        spreadsheet_id = stat.ident
        service = self._create_service()
        # pylint: disable=no-member
        resp = service.spreadsheets().get(
            spreadsheetId=stat.ident).execute()
        requests = []
        for sheet in resp['sheets']:
            if sheet['properties']['title'] != locale:
                continue
            sheet_id = sheet['properties']['sheetId']
            requests += self._generate_style_requests(
                sheet_id, sheet=sheet, catalog=catalog)
        self._perform_batch_update(spreadsheet_id, requests)

    def download(self, locales, save_stats=True, include_obsolete=False):
        """Override base download to remove the threading and simplify."""
        if not self.pod.file_exists(base.Translator.TRANSLATOR_STATS_PATH):
            text = 'File {} not found. Nothing to download.'
            self.pod.logger.info(text.format(base.Translator.TRANSLATOR_STATS_PATH))
            return
        stats_to_download = self._get_stats_to_download(locales)
        if not stats_to_download:
            return
        num_files = len(stats_to_download)
        text = 'Downloading translations: %(value)d/{} (in %(time_elapsed).9s)'
        widgets = [progressbar.FormatLabel(text.format(num_files))]
        bar = progressbar_non.create_progressbar(
            "Downloading translations...", widgets=widgets, max_value=num_files)
        bar.start()

        spreadsheet_id_to_locales = {}
        for locale in stats_to_download:

            stat = stats_to_download[locale]
            if stat.ident not in spreadsheet_id_to_locales:
                spreadsheet_id_to_locales[stat.ident] = set()
            spreadsheet_id_to_locales[stat.ident].add(locale)

        langs_to_translations = {}
        new_stats = []

        # Batch download for each sheet id.
        for spreadsheet_id in spreadsheet_id_to_locales:
            locales = spreadsheet_id_to_locales[spreadsheet_id]
            locale_to_values = self._download_sheets(spreadsheet_id, locales)

            for i, (lang, stat) in enumerate(stats_to_download.items()):
                if lang not in locale_to_values:
                    continue

                new_stat, content = self._download_content(stat, locale_to_values[lang])
                bar.update(bar.value + 1)
                new_stat.uploaded = stat.uploaded  # Preserve uploaded field.
                langs_to_translations[lang] = content
                new_stats.append(new_stat)

        bar.finish()

        text = 'Importing translations: %(value)d/{} (in %(time_elapsed).9s)'
        widgets = [progressbar.FormatLabel(text.format(num_files))]
        bar = progressbar_non.create_progressbar(
            "Importing translations...", widgets=widgets, max_value=num_files)
        bar.start()

        has_changed_content = False
        unchanged_locales = []
        changed_locales = {}
        for lang, translations in langs_to_translations.items():
            has_changed_content, imported_translations, total_translations = self.pod.catalogs.import_translations(
                    locale=lang, content=translations,
                    include_obsolete=include_obsolete)
            bar.update(bar.value + 1)
            if imported_translations == 0:
                unchanged_locales.append(lang)
            else:
                changed_locales[lang] = {
                    'imported': imported_translations,
                    'total': total_translations,
                }
            if has_changed_content:
                has_changed_content = True

        bar.finish()

        if save_stats and has_changed_content:
            self.save_stats(new_stats)
        self._log_catalog_changes(unchanged_locales, changed_locales)
        return new_stats

    def get_edit_url(self, doc):
        if not doc.locale:
            return
        stats = self._get_stats_to_download([doc.locale])
        if doc.locale not in stats:
            return
        stat = stats[doc.locale]
        return '{}&fvid={}'.format(stat.url, self._content_hash(doc.pod_path, doc.locale))
