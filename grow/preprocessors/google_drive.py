from . import base
from googleapiclient import discovery
from googleapiclient import errors
from grow.common import oauth
from grow.common import utils
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

    def _create_service(self):
        credentials = oauth.get_or_create_credentials(
            scope=OAUTH_SCOPE, storage_key='Grow SDK')
        http = httplib2.Http(ca_certs=utils.get_cacerts_path())
        http = credentials.authorize(http)
        return discovery.build('drive', 'v2', http=http)

    def run(self, build=True):
        try:
            self.download(self.config)
        except errors.HttpError as e:
            self.logger.error(str(e))


class GoogleDocsPreprocessor(BaseGooglePreprocessor):
    KIND = 'google_docs'

    class Config(messages.Message):
        path = messages.StringField(1)
        id = messages.StringField(2)
        convert = messages.BooleanField(3)

    def _process_google_hrefs(self, soup):
        for tag in soup.find_all('a'):
            if tag.attrs.get('href'):
                tag['href'] = self._clean_google_href(tag['href'])

    def _clean_google_href(self, href):
        regex = ('^'
                 + re.escape('https://www.google.com/url?q=')
                 + '(.*?)'
                 + re.escape('&'))
        match = re.match(regex, href)
        if match:
            encoded_url = match.group(1)
            return urllib.unquote(encoded_url)
        return href

    def download(self, config):
        doc_id = config.id
        path = config.path
        ext = os.path.splitext(config.path)[1]
        convert_to_markdown = ext == '.md' and config.convert is not False
        service = self._create_service()
        resp = service.files().get(fileId=doc_id).execute()
        for mimetype, url in resp['exportLinks'].iteritems():
            if mimetype.endswith('html'):
                resp, content = service._http.request(url)
                if resp.status != 200:
                    text = 'Error {} downloading Google Doc: {}'
                    self.logger.error(text.format(resp.status, path))
                    break
                soup = bs4.BeautifulSoup(content, 'html.parser')
                self._process_google_hrefs(soup)
                content = unicode(soup.body)
                if convert_to_markdown:
                    h2t = html2text.HTML2Text()
                    content = h2t.handle(content)
                content = content.encode('utf-8')
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
    def format_as_map(fp):
        reader = csv.reader(fp)
        results = {}

        def _update_node(root, part):
            if part not in root:
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
                parent[part] = value
            else:
                results[key] = value

        return results

    def download(self, config):
        path = config.path
        sheet_id = config.id
        service = self._create_service()
        resp = service.files().get(fileId=sheet_id).execute()
        ext = os.path.splitext(self.config.path)[1]
        convert_to = None
        if ext == '.json':
            convert_to = ext
            ext = '.csv'
        elif ext in ['.yaml', '.yml']:
            convert_to = ext
            ext = '.csv'
        if 'exportLinks' not in resp:
            text = 'Unable to export Google Sheet: {}'
            self.logger.error(text.format(path))
            self.logger.error('Received: {}'.format(resp))
            return
        for mimetype, url in resp['exportLinks'].iteritems():
            if not mimetype.endswith(ext[1:]):
                continue
            if self.config.gid:
                url += '&gid={}'.format(self.config.gid)
            resp, content = service._http.request(url)
            if resp.status != 200:
                text = 'Error {} downloading Google Sheet: {}'
                self.logger.error(text.format(resp.status, path))
                break
            if convert_to in ['.json', '.yaml', '.yml']:
                fp = cStringIO.StringIO()
                fp.write(content)
                fp.seek(0)
                kwargs = {}
                if self.config.format == 'map':
                    formatted_data = GoogleSheetsPreprocessor.format_as_map(fp)
                else:
                    reader = csv.DictReader(fp)
                    formatted_data = list(reader)
                if (path.endswith(('.yaml', '.yml'))
                        and self.config.preserve
                        and self.pod.file_exists(path)):
                    existing_data = self.pod.read_yaml(path)
                    if self.config.preserve == 'builtins':
                        for key in existing_data.keys():
                            if not key.startswith('$'):
                                del existing_data[key]
                    existing_data.update(formatted_data)
                    formatted_data = existing_data
                if convert_to == '.json':
                    if self.config.output_style == 'pretty':
                        kwargs['indent'] = 2
                        kwargs['separators'] = (',', ': ')
                        kwargs['sort_keys'] = True
                    content = json.dumps(formatted_data, **kwargs)
                else:
                    content = yaml.safe_dump(
                        formatted_data,
                        default_flow_style=False)
            self.pod.write_file(path, content)
            self.logger.info('Downloaded Google Sheet -> {}'.format(path))
