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
from googleapiclient import discovery
from googleapiclient import errors
from protorpc import messages
from grow.common import oauth
from grow.common import untag
from grow.common import utils
from grow.documents import document_format
from grow.documents import document_front_matter as doc_front_matter
from grow.preprocessors import base


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
        folder = messages.StringField(4)
        collection = messages.StringField(5)

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

    def _execute_doc(self, path, doc_id, convert):
        content = GoogleDocsPreprocessor.download(
            path, doc_id=doc_id, logger=self.pod.logger)
        existing_data = None
        if self.pod.file_exists(path):
            existing_data = self.pod.read_file(path)
        content = GoogleDocsPreprocessor.format_content(
            path, content, convert=convert, existing_data=existing_data)
        self.pod.write_file(path, content)
        self.logger.info('Downloaded Google Doc -> {}'.format(path))

    def execute(self, config):
        convert = config.convert is not False
        # Binds a Google Drive folder to a collection.
        if config.folder:
            service = BaseGooglePreprocessor.create_service()
            query = "'{}' in parents".format(config.folder)
            # pylint: disable=no-member
            resp = service.files().list(q=query).execute()
            docs_to_add = []
            existing_docs = self.pod.list_dir(config.collection)
            for item in resp['items']:
                if item['mimeType'] != 'application/vnd.google-apps.document':
                    continue
                doc_id = item['id']
                title = item['title']
                if title.startswith(IGNORE_INITIAL):
                    self.pod.logger.info('Skipping -> {}'.format(title))
                    continue
                basename = '{}.md'.format(utils.slugify(title))
                docs_to_add.append(basename)
                path = os.path.join(config.collection, basename)
                self._execute_doc(path, doc_id, convert)
            # Clean up files that are no longer in Google Drive.
            for path in existing_docs:
                if path.lstrip('/') not in docs_to_add:
                    path_to_delete = os.path.join(
                            config.collection, path.lstrip('/'))
                    self.pod.delete_file(path_to_delete)
                    text = 'Deleting -> {}'.format(path_to_delete)
                    self.pod.logger.info(text)
            return
        # Downloads a single document.
        doc_id = config.id
        path = config.path
        self._execute_doc(config.path, doc_id, convert)

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
        header_row_count = messages.IntegerField(11, default=1)
        header_row_index = messages.IntegerField(12, default=1)

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
                 generate_ids=False, header_row_count=1, header_row_index=1):
        logger = logger or logging
        # Show metadata about the file to help the user better understand what
        # they are downloading. Also include a link in the output to permit the
        # user to quickly open the file.
        drive_service = BaseGooglePreprocessor.create_service('drive', 'v3')
        # pylint: disable=no-member
        resp = drive_service.files().get(
            fileId=spreadsheet_id,
            fields='name,modifiedTime,lastModifyingUser,webViewLink').execute()
        if 'lastModifyingUser' in resp:
            # Sometimes the email address isn't included.
            name = resp['lastModifyingUser']['displayName']
            modified_by = resp['lastModifyingUser'].get('emailAddress', name)
            logger.info('Downloading "{}" modified {} by {} from {}'.format(
                resp['name'],
                resp['modifiedTime'],
                modified_by,
                resp['webViewLink']))
        else:
            logger.info('Downloading "{}" modified {} from {}'.format(
                resp['name'],
                resp['modifiedTime'],
                resp['webViewLink']))

        service = BaseGooglePreprocessor.create_service('sheets', 'v4')
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
                header_rows = []
                for row in resp['values']:
                    if len(header_rows) < header_row_count:
                        header_rows.append(row)
                        # Only one of the header rows are the actual headers.
                        if len(header_rows) == header_row_index:
                            if format_as_grid:
                                # Ignore first column as a header.
                                headers = row[1:]
                            else:
                                headers = row
                        continue

                    if format_as_grid:
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
                                if not grid_key or grid_key.startswith(IGNORE_INITIAL):
                                    continue
                                if isinstance(grid_key, unicode):
                                    grid_key = grid_key.encode('utf-8')
                                value = (row[col] if row_len > col else '').strip()
                                if value:
                                    grid_obj[grid_key] = value
                            gid_to_data[gid][key] = grid_obj
                    elif format_as_map:
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
                # Do a text parse of the yaml file to prevent the constructors.
                content = self.pod.read_file(path)
                existing_data = utils.load_plain_yaml(content)
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
            logger=self.pod.logger, generate_ids=config.generate_ids,
            header_row_count=config.header_row_count,
            header_row_index=config.header_row_index)

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
                # Use plain text dumper to preserve yaml constructors.
                output_content = utils.dump_plain_yaml(gid_to_data[gid])
                self.pod.write_file(output_path, output_content)
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
            # Use plain text dumper to preserve yaml constructors.
            return utils.dump_plain_yaml(formatted_data)
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

                gid_to_data[gid] = untag.Untag.untag(gid_to_data[gid])
                doc.inject(fields=gid_to_data[gid])
        else:
            # TODO Multi sheet import.
            pass

    def get_edit_url(self, doc=None):
        """Returns the URL to edit in Google Sheets."""
        gid = self.config.gid or '0'
        return GoogleSheetsPreprocessor._edit_url_format.format(
            id=self.config.id, gid=gid)
