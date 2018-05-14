"""
    Google Drive (Sheets and Docs) preprocessors allow you to store content in
    Google Drive and bring it into Grow. Grow will authenticate to the Google
    Drive API using OAuth2 and then download content as specified in
    `podspec.yaml`.

    Grow supports various ways to transform the content, e.g. Sheets can be
    downloaded and converted to yaml, and Docs can be downloaded and converted
    to markdown.
"""

import cStringIO
import csv
import json
import logging
import os
import httplib2
import yaml
from googleapiclient import discovery
from googleapiclient import errors
from grow.common import oauth
from grow.common import utils
from grow.documents import document_fields
from grow.documents import document_format
from grow.documents import document_front_matter as doc_front_matter
from protorpc import messages
from . import base


OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
STORAGE_KEY = 'Grow SDK'
IGNORE_INITIAL = ('_', '#')


# Silence extra logging from googleapiclient.
discovery.logger.setLevel(logging.WARNING)


class BaseGooglePreprocessor(base.BasePreprocessor):

    @staticmethod
    def create_service(api='drive', version='v2'):
        credentials = oauth.get_or_create_credentials(
            scope=OAUTH_SCOPE, storage_key='Grow SDK')
        http = httplib2.Http(ca_certs=utils.get_cacerts_path())
        http = credentials.authorize(http)
        return discovery.build(api, version, http=http)

    def run(self, build=True):
        try:
            self.execute(self.config)
        except errors.HttpError as e:
            self.logger.error(str(e))

    def execute(self, config):
        raise NotImplementedError


class GoogleDocsPreprocessor(BaseGooglePreprocessor):
    KIND = 'google_docs'
    _edit_url_format = 'https://docs.google.com/document/d/{id}/edit'

    class Config(messages.Message):
        path = messages.StringField(1)
        id = messages.StringField(2)
        convert = messages.BooleanField(3)

    @classmethod
    def download(cls, path, doc_id, logger=None, raise_errors=False):
        logger = logger or logging
        service = BaseGooglePreprocessor.create_service()
        # pylint: disable=no-member
        resp = service.files().get(fileId=doc_id).execute()
        if 'exportLinks' not in resp:
            text = 'Unable to export Google Doc: {}'
            logger.error(text.format(path))
            logger.error('Received: {}'.format(resp))
            return
        for mimetype, url in resp['exportLinks'].iteritems():
            if not mimetype.endswith('html'):
                continue
            resp, content = service._http.request(url)
            if resp.status != 200:
                text = 'Error {} downloading Google Doc: {}'
                text = text.format(resp.status, path)
                if raise_errors:
                    raise base.PreprocessorError(text)
                logger.error(text)
            return content
        if raise_errors:
            text = 'No file to export from Google Docs: {}'.format(path)
            raise base.PreprocessorError(text)

    @classmethod
    def format_content(cls, path, content, convert=True, existing_data=None):
        ext = os.path.splitext(path)[1]
        convert_to_markdown = ext == '.md' and convert is not False
        content = utils.clean_html(
            content, convert_to_markdown=convert_to_markdown)
        # Preserve any existing frontmatter, return new content.
        if existing_data:
            if doc_front_matter.BOUNDARY_REGEX.search(existing_data):
                front_matter, old_content = doc_front_matter.DocumentFrontMatter.split_front_matter(
                    existing_data)
                return document_format.DocumentFormat.format_doc(front_matter, content)
        return content

    def execute(self, config):
        doc_id = config.id
        path = config.path
        convert = config.convert is not False
        content = GoogleDocsPreprocessor.download(
            path, doc_id=doc_id, logger=self.pod.logger)
        existing_data = None
        if self.pod.file_exists(path):
            existing_data = self.pod.read_file(path)
        content = GoogleDocsPreprocessor.format_content(
            path, content, convert=convert, existing_data=existing_data)
        self.pod.write_file(path, content)
        self.logger.info('Downloaded Google Doc -> {}'.format(path))

    def get_edit_url(self, doc=None):
        """Returns the URL to edit in Google Docs."""
        return GoogleDocsPreprocessor._edit_url_format.format(id=self.config.id)


class GoogleSheetsPreprocessor(BaseGooglePreprocessor):
    KIND = 'google_sheets'
    GRID_TYPES = ['grid']
    MAP_TYPES = ['map', 'strings']
    _sheet_edit_url_format = 'https://docs.google.com/spreadsheets/d/{id}/edit'
    _edit_url_format = 'https://docs.google.com/spreadsheets/d/{id}/edit#gid={gid}'

    class Config(messages.Message):
        path = messages.StringField(1)
        id = messages.StringField(2)
        gid = messages.IntegerField(3)
        output_style = messages.StringField(4, default='compressed')
        format = messages.StringField(5, default='list')
        preserve = messages.StringField(6, default='builtins')
        gids = messages.IntegerField(7, repeated=True)
        collection = messages.StringField(8)
        output_format = messages.StringField(9, default='yaml')
        generate_ids = messages.BooleanField(10, default=False)

    @staticmethod
    def _convert_rows_to_mapping(reader):
        results = {}

        def _update_node(root, part):
            if isinstance(root, dict) and part not in root:
                root[part] = {}
        for row in reader:
            key = row[0]
            value = row[1]
            if key.startswith(IGNORE_INITIAL):
                continue
            if '.' in key:
                parts = key.split('.')
                parent = results
                for i, part in enumerate(parts):
                    _update_node(parent, part)
                    if i + 1 < len(parts):
                        parent = parent[part]
                if isinstance(parent, dict):
                    parent[part] = value
            else:
                results[key] = value
        return results

    @staticmethod
    def column_to_letter(column_num):
        div = column_num
        string = ""
        temp = 0
        while div > 0:
            module = (div - 1) % 26
            string = chr(65 + module) + string
            div = int((div - module) / 26)
        return string

    @staticmethod
    def format_as_map(fp):
        reader = csv.reader(fp)
        results = GoogleSheetsPreprocessor._convert_rows_to_mapping(reader)
        return results

    @classmethod
    def download(cls, spreadsheet_id, gids=None, format_as='list', logger=None,
                 generate_ids=False):
        service = BaseGooglePreprocessor.create_service('sheets', 'v4')
        logger = logger or logging
        format_as_grid = format_as in cls.GRID_TYPES
        format_as_map = format_as in cls.MAP_TYPES
        # pylint: disable=no-member
        spreadsheet = service.spreadsheets().get(
            spreadsheetId=spreadsheet_id).execute()

        gid_to_sheet = {}
        for sheet in spreadsheet['sheets']:
            gid_to_sheet[sheet['properties']['sheetId']] = sheet['properties']

        if not gids:
            gids = gid_to_sheet.keys()
        if gids and len(gids) > 1:
            url = GoogleSheetsPreprocessor._sheet_edit_url_format.format(id=spreadsheet_id)
            logger.info('Downloading {} tabs -> {}'.format(len(gids), url))

        gid_to_data = {}
        generated_key_index = 0
        for gid in gids:
            if format_as_map:
                max_column = 'B'
            else:
                max_column = GoogleSheetsPreprocessor.column_to_letter(
                    gid_to_sheet[gid]['gridProperties']['columnCount'])
            range_name = "'{}'!A:{}".format(
                gid_to_sheet[gid]['title'], max_column)

            # pylint: disable=no-member
            resp = service.spreadsheets().values().get(
                spreadsheetId=spreadsheet_id, range=range_name).execute()

            if format_as_map or format_as_grid:
                gid_to_data[gid] = {}
            else:
                gid_to_data[gid] = []

            if not 'values' in resp:
                logger.info(
                    'No values found in sheet -> {}'.format(gid_to_sheet[gid]['title']))
            else:
                title = gid_to_sheet[gid]['title']
                if title.startswith(IGNORE_INITIAL):
                    logger.info('Skipping tab -> {}'.format(title))
                    continue
                headers = None
                for row in resp['values']:
                    if format_as_grid:
                        if not headers:
                            # Ignore first column as a header.
                            headers = row[1:]
                            continue
                        if not row:  # Skip empty rows.
                            continue
                        key = row[0].strip()
                        if isinstance(key, unicode):
                            key = key.encode('utf-8')
                        if key and key in gid_to_data[gid]:
                            # The key is already in use.
                            raise base.PreprocessorError(
                                'Duplicate key in use in sheet {}: {}'.format(gid, key))
                        if key and not key.startswith(IGNORE_INITIAL):
                            # Grids use the first column as the key and make
                            # object out of the remaining columns.
                            grid_obj = {}
                            row = row[1:]
                            row_len = len(row)
                            for col, grid_key in enumerate(headers):
                                if isinstance(grid_key, unicode):
                                    grid_key = grid_key.encode('utf-8')
                                value = (row[col] if row_len > col else '').strip()
                                if value:
                                    grid_obj[grid_key] = value
                            gid_to_data[gid][key] = grid_obj
                    elif format_as_map:
                        if not headers:
                            headers = row
                            continue
                        if not row:  # Skip empty rows.
                            continue
                        key = row[0].strip()
                        if isinstance(key, unicode):
                            key = key.encode('utf-8')
                        if not key and generate_ids:
                            key = 'untranslated_{}'.format(generated_key_index)
                            generated_key_index += 1
                        if key and not key.startswith(IGNORE_INITIAL):
                            if format_as == 'strings' and '@' not in key:
                                key = '{}@'.format(key)
                            gid_to_data[gid][key] = (
                                row[1] if len(row) == 2 else '')
                    else:
                        if not headers:
                            headers = row
                            continue
                        row_values = {}
                        for idx, column in enumerate(headers):
                            if not column.startswith(IGNORE_INITIAL):
                                row_values[column] = (
                                    row[idx] if len(row) > idx else '')
                        gid_to_data[gid].append(row_values)
        return gid_to_sheet, gid_to_data

    @staticmethod
    def parse_path(path):
        if ':' in path:
            return path.rsplit(':', 1)
        return path, None

    def _maybe_preserve_content(self, new_data, path, key_to_update):
        if path.endswith(('.yaml', '.yml')) and self.config.preserve:
            # Use existing data if it exists. If we're updating data at a
            # specific key, and if the existing data doesn't exist, use an
            # empty dict. If the file doesn't exist and if we're not updating
            # at a specific key, just return the new data without reformatting.
            if self.pod.file_exists(path):
                existing_data = self.pod.read_yaml(path)
            elif key_to_update:
                existing_data = {}
            else:
                return new_data
            # Skip trying to update lists, because there would be no
            # expectation of merging old and new list data.
            if not key_to_update and not isinstance(new_data, dict):
                return new_data
            if isinstance(existing_data, dict):
                return utils.format_existing_data(
                    old_data=existing_data, new_data=new_data,
                    preserve=self.config.preserve, key_to_update=key_to_update)
        return new_data


    def execute(self, config):
        spreadsheet_id = config.id
        gids = config.gids or []
        if config.gid is not None:
            gids.append(config.gid)
        if not gids and not config.collection:
            gids.append(0)
        format_as = config.format
        if (config.collection and
                format_as not in GoogleSheetsPreprocessor.MAP_TYPES and
                format_as not in GoogleSheetsPreprocessor.GRID_TYPES):
            format_as = 'map'
        gid_to_sheet, gid_to_data = GoogleSheetsPreprocessor.download(
            spreadsheet_id=spreadsheet_id, gids=gids, format_as=format_as,
            logger=self.pod.logger, generate_ids=config.generate_ids)

        if config.path:
            # Single sheet import.
            path, key_to_update = self.parse_path(config.path)

            for gid in gids:
                # Preserve existing data if necessary.
                gid_to_data[gid] = self._maybe_preserve_content(
                        new_data=gid_to_data[gid],
                        path=path,
                        key_to_update=key_to_update)
                content = GoogleSheetsPreprocessor.serialize_content(
                    formatted_data=gid_to_data[gid], path=path,
                    output_style=self.config.output_style)

                self.pod.write_file(path, content)
                self.logger.info(
                    'Downloaded {} ({}) -> {}'.format(
                        gid_to_sheet[gid]['title'], gid, path))
        else:
            # Multi sheet import based on collection.
            collection_path = config.collection

            if not gids:
                gids = gid_to_sheet.keys()

            for gid in gids:
                if gid_to_sheet[gid]['title'].strip().startswith(IGNORE_INITIAL):
                    continue
                file_name = '{}.yaml'.format(
                    utils.slugify(gid_to_sheet[gid]['title']))
                output_path = os.path.join(collection_path, file_name)
                gid_to_data[gid] = self._maybe_preserve_content(
                        new_data=gid_to_data[gid],
                        path=output_path,
                        key_to_update=None)
                self.pod.write_yaml(output_path, gid_to_data[gid])
                self.logger.info(
                    'Downloaded {} ({}) -> {}'.format(
                        gid_to_sheet[gid]['title'], gid, output_path))

    @classmethod
    def get_convert_to(cls, path):
        ext = os.path.splitext(path)[1]
        convert_to = None
        if ext == '.json':
            return ext
        elif ext in ['.yaml', '.yml']:
            return ext
        return convert_to

    @classmethod
    def format_content(cls, content, path, format_as=None, preserve=None,
                       existing_data=None, key_to_update=None):
        """Formats content into either a CSV (text), list, or dictionary."""
        convert_to = cls.get_convert_to(path)
        if convert_to in ['.json', '.yaml', '.yml']:
            fp = cStringIO.StringIO()
            fp.write(content)
            fp.seek(0)
            if format_as == 'map':
                formatted_data = GoogleSheetsPreprocessor.format_as_map(fp)
            else:
                reader = csv.DictReader(fp)
                formatted_data = list(reader)
            formatted_data = utils.format_existing_data(
                old_data=existing_data, new_data=formatted_data,
                preserve=preserve, key_to_update=key_to_update)
            return formatted_data
        return content

    @classmethod
    def serialize_content(cls, formatted_data, path, output_style=None):
        """Serializes an object into a string as JSON, YAML, or a CSV
        (default)."""
        kwargs = {}
        convert_to = cls.get_convert_to(path)
        if convert_to == '.json':
            if output_style == 'pretty':
                kwargs['indent'] = 2
                kwargs['separators'] = (',', ': ')
                kwargs['sort_keys'] = True
            return json.dumps(formatted_data, **kwargs)
        elif convert_to in ('.yaml', '.yml'):
            return yaml.safe_dump(formatted_data, default_flow_style=False)
        return formatted_data

    def can_inject(self, doc=None, collection=None):
        if not self.injected:
            return False
        path, key_to_update = self.parse_path(self.config.path)
        if doc and doc.pod_path == path:
            return True
        return False

    def _normalize_formatted_content(self, fields):
        # A hack that sends fields through a roundtrip json serialization to
        # avoid encoding issues with injected output from Google Sheets.
        fp = cStringIO.StringIO()
        json.dump(fields, fp)
        fp.seek(0)
        return json.load(fp)

    def inject(self, doc):
        spreadsheet_id = self.config.id
        gids = self.config.gids or []
        if self.config.gid is not None:
            gids.append(self.config.gid)
        format_as = self.config.format
        if self.config.collection and format_as not in self.MAP_TYPES:
            format_as = 'map'
        _, gid_to_data = GoogleSheetsPreprocessor.download(
            spreadsheet_id=spreadsheet_id, gids=gids, format_as=format_as,
            logger=self.pod.logger, generate_ids=self.config.generate_ids)

        if self.config.path:
            if format_as in ['list']:
                self.pod.logger.info(
                    'Cannot inject list formatted spreadsheet -> {}'.format(self.config.path))
                return
            # Single sheet import.
            path, key_to_update = self.parse_path(self.config.path)

            for gid in gids:
                # Preserve existing yaml data.
                if (path.endswith(('.yaml', '.yml'))
                        and self.config.preserve and self.pod.file_exists(path)):
                    existing_data = self.pod.read_yaml(path)
                    gid_to_data[gid] = utils.format_existing_data(
                        old_data=existing_data, new_data=gid_to_data[gid],
                        preserve=self.config.preserve, key_to_update=key_to_update)

                gid_to_data[gid] = document_fields.DocumentFields.untag(gid_to_data[
                                                                        gid])
                doc.inject(fields=gid_to_data[gid])
        else:
            # TODO Multi sheet import.
            pass

    def get_edit_url(self, doc=None):
        """Returns the URL to edit in Google Sheets."""
        gid = self.config.gid or '0'
        return GoogleSheetsPreprocessor._edit_url_format.format(
            id=self.config.id, gid=gid)
