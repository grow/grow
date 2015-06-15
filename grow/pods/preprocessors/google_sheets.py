from googleapiclient import discovery
from googleapiclient import errors
from grow.common import utils
from grow.pods.preprocessors import base
from oauth2client import client
from oauth2client import keyring_storage
from oauth2client import tools
from protorpc import messages
import cStringIO
import csv
import httplib2
import json
import logging
import os

# Google API details for a native/installed application for API project grow-prod.
CLIENT_ID = '578372381550-jfl3hdlf1q5rgib94pqsctv1kgkflu1a.apps.googleusercontent.com'
CLIENT_SECRET = 'XQKqbwTg88XVpaBNRcm_tYLf'  # Not so secret for installed apps.
OAUTH_SCOPE = 'https://www.googleapis.com/auth/drive'
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

# Silence extra logging from googleapiclient.
discovery.logger.setLevel(logging.WARNING)


class Config(messages.Message):
  path = messages.StringField(1)
  id = messages.StringField(2)
  gid = messages.IntegerField(3)


class GoogleSheetsPreprocessor(base.BasePreprocessor):
  KIND = 'google_sheets'
  Config = Config

  def run(self):
    try:
      self.download(path=self.config.path, sheet_id=self.config.id,
                    sheet_gid=self.config.gid)
    except errors.HttpError as e:
      self.logger.error(str(e))

  def download(self, path, sheet_id, sheet_gid):
    credentials = self._get_credentials()
    http = httplib2.Http(ca_certs=utils.get_cacerts_path())
    http = credentials.authorize(http)
    service = discovery.build('drive', 'v2', http=http)
    resp = service.files().get(fileId=sheet_id).execute()
    ext = os.path.splitext(self.config.path)[1]
    convert_to = None
    if ext == '.json':
      ext = '.csv'
      convert_to = '.json'
    for mimetype, url in resp['exportLinks'].iteritems():
      if not mimetype.endswith(ext[1:]):
        continue
      if self.config.gid:
        url += '&gid={}'.format(self.config.gid)
      resp, content = service._http.request(url)
      if resp.status != 200:
        self.logger.error('Error downloading Google Sheet: {}'.format(path))
        break
      if convert_to == '.json':
        fp = cStringIO.StringIO()
        fp.write(content)
        fp.seek(0)
        reader = csv.DictReader(fp)
        content = json.dumps([row for row in reader])
      self.pod.write_file(path, content)
      self.logger.info('Downloaded Google Sheet -> {}'.format(path))

  def _get_credentials(self, username='default'):
    storage = keyring_storage.Storage('Grow SDK', username)
    credentials = storage.get()
    if credentials is None:
      parser = tools.argparser
      flags, _ = parser.parse_known_args(['--noauth_local_webserver'])
      flow = client.OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, OAUTH_SCOPE,
                                        redirect_uri=REDIRECT_URI)
      credentials = tools.run_flow(flow, storage, flags)
    return credentials
