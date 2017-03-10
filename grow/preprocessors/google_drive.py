"""
    Google Drive (Sheets and Docs) preprocessors allow you to store content in
    Google Drive and bring it into Grow. Grow will authenticate to the Google
    Drive API using OAuth2 and then download content as specified in
    `podspec.yaml`.

    Grow supports various ways to transform the content, e.g. Sheets can be
    downloaded and converted to yaml, and Docs can be downloaded and converted
    to markdown.
"""

from . import base
from googleapiclient import discovery
from googleapiclient import errors
from grow.common import oauth
from grow.common import utils
from grow.pods import document_fields
from protorpc import messages
import cStringIO
import csv
import httplib2
import json
import logging
import os
import yaml


OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
STORAGE_KEY = 'Grow SDK'


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
        content = utils.clean_html(content, convert_to_markdown=convert_to_markdown)
        # Preserve any existing frontmatter.
        if existing_data:
            if formats.Format.has_front_matter(existing_data):
                content = formats.Format.update(
                    existing_data, body=content)
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
    _edit_url_format = 'https://docs.google.com/spreadsheets/d/{id}/edit#gid={gid}'

    class Config(messages.Message):
        path = messages.StringField(1)
        id = messages.StringField(2)
        gid = messages.IntegerField(3)
        output_style = messages.StringField(4, default='compressed')
        format = messages.StringField(5, default='list')
        preserve = messages.StringField(6, default='builtins')

    @staticmethod
    def _convert_rows_to_mapping(reader):
        results = {}
        def _update_node(root, part):
            if isinstance(root, dict) and part not in root:
                root[part] = {}
        for row in reader:
            key = row[0]
            value = row[1]
            if key.startswith('#'):
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
    def format_as_map(fp):
        reader = csv.reader(fp)
        results = GoogleSheetsPreprocessor._convert_rows_to_mapping(reader)
        return results

    @classmethod
    def download(cls, path, sheet_id, gid=None, logger=None,
                 raise_errors=False):
        logger = logger or logging
        ext = os.path.splitext(path)[1]
        service = BaseGooglePreprocessor.create_service()
        resp = service.files().get(fileId=sheet_id).execute()
        if 'exportLinks' not in resp:
            text = 'Unable to export Google Sheet: {} / Received: {}'
            logger.error(text.format(path, resp))
            if raise_errors:
                raise base.PreprocessorError(text)
            return
        for mimetype, url in resp['exportLinks'].iteritems():
            if not mimetype.endswith('csv'):
                continue
            if gid is not None:
                url += '&gid={}'.format(gid)
            resp, content = service._http.request(url)
            if resp.status != 200:
                text = 'Error {} downloading Google Sheet: {}'
                text = text.format(resp.status, path)
                logger.error(text)
                if raise_errors:
                    raise base.PreprocessorError(text)
            # Weak test to defend against critical errors while still
            # permitting 404s. We may want to remove the "raise_errors = False"
            # code path in its entirety in the future.
            # https://github.com/grow/grow/issues/283
            if content.startswith('<!DOCTYPE'):
                text = 'Error downloading Google Sheet. Received: {}'
                raise base.PreprocessorError(text.format(content))
            return content
        if raise_errors:
            text = 'No file to export from Google Sheets: {}'.format(path)
            raise base.PreprocessorError(text)

    def _parse_path(self, path):
        if ':' in path:
            return path.rsplit(':', 1)
        return path, None

    def execute(self, config):
        path, key_to_update = self._parse_path(config.path)
        sheet_id = config.id
        gid = config.gid
        content = GoogleSheetsPreprocessor.download(
            path=path, sheet_id=sheet_id, gid=gid, logger=self.pod.logger)
        existing_data = None
        if (path.endswith(('.yaml', '.yml'))
                and self.config.preserve
                and self.pod.file_exists(path)):
            existing_data = self.pod.read_yaml(path)
        content = GoogleSheetsPreprocessor.format_content(
            content=content, path=path, format_as=self.config.format,
            preserve=self.config.preserve,
            existing_data=existing_data, key_to_update=key_to_update)
        content = GoogleSheetsPreprocessor.serialize_content(
            formatted_data=content, path=path,
            output_style=self.config.output_style)
        self.pod.write_file(path, content)
        self.logger.info('Downloaded Google Sheet -> {}'.format(path))

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
        path, key_to_update = self._parse_path(self.config.path)
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
        path, key_to_update = self._parse_path(self.config.path)
        try:
            content = GoogleSheetsPreprocessor.download(
                path=path, sheet_id=self.config.id, gid=self.config.gid,
                raise_errors=True)
        except (errors.HttpError, base.PreprocessorError):
            doc.pod.logger.error('Error downloading sheet -> %s', path)
            raise
        if not content:
            return
        existing_data = doc.pod.read_yaml(doc.pod_path)
        fields = GoogleSheetsPreprocessor.format_content(
            content, path=path, format_as=self.config.format,
            preserve=self.config.preserve, existing_data=existing_data,
            key_to_update=key_to_update)
        fields = self._normalize_formatted_content(fields)
        fields = document_fields.DocumentFields._untag(fields)
        doc.inject(fields=fields)

    def get_edit_url(self, doc=None):
        """Returns the URL to edit in Google Sheets."""
        gid = self.config.gid or '0'
        return GoogleSheetsPreprocessor._edit_url_format.format(
            id=self.config.id, gid=gid)
