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
from grow.pods import formats
from protorpc import messages
import bs4
import cStringIO
import csv
import html2text
import httplib2
import json
import logging
import os
import re
import urllib
import yaml


OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'


# Silence extra logging from googleapiclient.
discovery.logger.setLevel(logging.WARNING)


class BaseGooglePreprocessor(base.BasePreprocessor):
    scheduleable = True

    @staticmethod
    def create_service():
        credentials = oauth.get_or_create_credentials(
            scope=OAUTH_SCOPE, storage_key='Grow SDK')
        http = httplib2.Http(ca_certs=utils.get_cacerts_path())
        http = credentials.authorize(http)
        return discovery.build('drive', 'v2', http=http)

    def run(self, build=True):
        try:
            self.execute(self.config)
        except errors.HttpError as e:
            self.logger.error(str(e))

    def execute(self, config):
        raise NotImplementedError


class GoogleDocsPreprocessor(BaseGooglePreprocessor):
    KIND = 'google_docs'

    class Config(messages.Message):
        path = messages.StringField(1)
        id = messages.StringField(2)
        convert = messages.BooleanField(3)

    @classmethod
    def _process_google_hrefs(cls, soup):
        for tag in soup.find_all('a'):
            if tag.attrs.get('href'):
                tag['href'] = cls._clean_google_href(tag['href'])

    @classmethod
    def _clean_google_href(cls, href):
        regex = ('^'
                 + re.escape('https://www.google.com/url?q=')
                 + '(.*?)'
                 + re.escape('&'))
        match = re.match(regex, href)
        if match:
            encoded_url = match.group(1)
            return urllib.unquote(encoded_url)
        return href

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
        soup = bs4.BeautifulSoup(content, 'html.parser')
        GoogleDocsPreprocessor._process_google_hrefs(soup)
        content = unicode(soup.body)
        if convert_to_markdown:
            h2t = html2text.HTML2Text()
            content = h2t.handle(content)
        content = content.encode('utf-8')
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


class GoogleSheetsPreprocessor(BaseGooglePreprocessor):
    KIND = 'google_sheets'

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
            if gid:
                url += '&gid={}'.format(gid)
            resp, content = service._http.request(url)
            if resp.status != 200:
                text = 'Error {} downloading Google Sheet: {}'
                text = text.format(resp.status, path)
                logger.error(text)
                if raise_errors:
                    raise base.PreprocessorError(text)
            return content
        if raise_errors:
            text = 'No file to export from Google Sheets: {}'.format(path)
            raise base.PreprocessorError(text)

    def execute(self, config):
        path = config.path
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
            existing_data=existing_data)
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
                       existing_data=None):
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
            if existing_data:
                if preserve == 'builtins':
                    for key in existing_data.keys():
                        if not key.startswith('$'):
                            del existing_data[key]
                existing_data.update(formatted_data)
                formatted_data = existing_data
            return formatted_data
        return content

    @classmethod
    def serialize_content(cls, formatted_data, path, output_style=None):
        kwargs = {}
        convert_to = cls.get_convert_to(path)
        if convert_to == '.json':
            if output_style == 'pretty':
                kwargs['indent'] = 2
                kwargs['separators'] = (',', ': ')
                kwargs['sort_keys'] = True
            return json.dumps(formatted_data, **kwargs)
        else:
            return yaml.safe_dump(
                formatted_data,
                default_flow_style=False)
