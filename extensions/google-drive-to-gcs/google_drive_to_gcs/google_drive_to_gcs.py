"""Grow extension for syncing Google Drive files to Google Cloud Storage."""

import io
import logging
import re
import time
import urllib.parse

import httplib2
import jinja2
from googleapiclient import discovery, http
from googleapiclient.http import MediaIoBaseDownload
from jinja2.ext import Extension

from grow.common import oauth, utils
from grow.preprocessors import google_drive

GCS_UPLOAD_CHUNKSIZE = 10 * 1024 * 1024
NUM_RETRIES = 2
BACKOFF = 4
ERRORS_TO_RETRY = (OSError, httplib2.HttpLib2Error, KeyError)

STORAGE_KEY = 'Grow SDK - Drive to GCS'
SCOPES = [
    'https://www.googleapis.com/auth/devstorage.full_control',
]

_FILE_ID_RE = re.compile(r'^[A-Za-z0-9_-]+$')
_DRIVE_FILE_PATH_RE = re.compile(r'/file/d/([A-Za-z0-9_-]+)')


def url_to_file_id(url):
    """Extracts and validates a Google Drive file ID from a Drive share URL."""
    parsed = urllib.parse.urlsplit(url or '')
    if parsed.scheme not in ('http', 'https') or parsed.hostname not in (
        'drive.google.com',
        'docs.google.com',
    ):
        raise ValueError(f'Unsupported Google Drive URL: {url!r}')

    match = _DRIVE_FILE_PATH_RE.search(parsed.path)
    if match:
        file_id = match.group(1)
    else:
        qs = urllib.parse.parse_qs(parsed.query)
        file_id = qs.get('id', [''])[0]

    if not file_id or not _FILE_ID_RE.match(file_id):
        raise ValueError(f'Unable to extract valid Drive file ID from: {url!r}')
    return file_id


def download_google_drive_file(service, file_id):
    if not _FILE_ID_RE.match(file_id or ''):
        raise ValueError(f'Invalid Drive file ID: {file_id!r}')
    request = service.files().get_media(fileId=file_id)
    fh = io.BytesIO()
    downloader = MediaIoBaseDownload(fh, request)
    completed = False
    while completed is False:
        status, completed = downloader.next_chunk()
        logging.info(
            'Downloading from Google Drive -> %s %d%%',
            file_id,
            int(status.progress() * 100),
        )
    fh.seek(0)
    return fh


def upload_google_storage_file(service, gs_path, fp, mimetype=None):
    bucket, path = gs_path.lstrip('/').split('/', 1)
    if not bucket or not path or '..' in path.split('/'):
        raise ValueError(f'Invalid GCS path: {gs_path!r}')
    fp.seek(0)
    media = http.MediaIoBaseUpload(
        fp, chunksize=GCS_UPLOAD_CHUNKSIZE, mimetype=mimetype, resumable=True
    )
    logging.info('Uploading to Google Cloud Storage -> %s:%s', bucket, path)
    req = service.objects().insert(media_body=media, name=path, bucket=bucket)
    resp = None
    backoff = BACKOFF
    retries = 0
    connections = 0
    last_error = None
    while resp is None:
        try:
            _, resp = req.next_chunk()
            backoff = BACKOFF
            connections += 1
            continue
        except ERRORS_TO_RETRY as e:
            last_error = e
            logging.warning('GCS upload encountered error to retry: %s', e)
        retries += 1
        if retries > NUM_RETRIES:
            raise ValueError(f'Hit max retry attempts with error: {last_error}')
        time.sleep(backoff)
        backoff *= 2
    logging.info('Uploaded in %s tries -> %s', connections, gs_path)
    return f'/{bucket}/{path}'


class GoogleDriveSyncer:
    def __init__(self, pod):
        self.pod = pod
        self._cache = None

    def __repr__(self):
        return '<GoogleDriveSyncer>'

    @property
    def cache(self):
        if self._cache is None:
            podcache = self.pod.podcache
            ident = 'ext-google-drive-to-gcs'
            self._cache = podcache.get_object_cache(ident, write_to_file=True)
        return self._cache

    @property
    def drive_service(self):
        return google_drive.BaseGooglePreprocessor.create_service('drive', 'v3')

    @property
    def storage_service(self):
        credentials = oauth.get_or_create_credentials(scope=SCOPES, storage_key=STORAGE_KEY)
        http_client = httplib2.Http(ca_certs=utils.get_cacerts_path())
        http_client = credentials.authorize(http_client)
        return discovery.build('storage', 'v1', http=http_client)

    def execute(self, file_id, bucket_path):
        if not _FILE_ID_RE.match(file_id or ''):
            raise ValueError(f'Invalid Drive file ID: {file_id!r}')
        result = self.cache.get(file_id)
        if result is None:
            bucket_path = bucket_path.rstrip('/')
            gs_path = f'{bucket_path}/{file_id}'
            fh = download_google_drive_file(self.drive_service, file_id)
            mimetype = 'image/jpeg'
            gs_path = upload_google_storage_file(self.storage_service, gs_path, fh, mimetype)
            result = {
                'gs_path': gs_path,
            }
            self.cache.add(file_id, result)
        return result


class GoogleDriveToGCSExtension(Extension):
    def __init__(self, environment):
        super().__init__(environment)
        environment.globals['google_drive_to_gcs'] = GoogleDriveToGCSExtension.do_drive_to_gcs

    @staticmethod
    @jinja2.pass_context
    def do_drive_to_gcs(ctx, bucket_path, drive_url):
        pod = ctx['doc'].pod
        file_id = url_to_file_id(drive_url)
        syncer = GoogleDriveSyncer(pod)
        return syncer.execute(file_id, bucket_path)
