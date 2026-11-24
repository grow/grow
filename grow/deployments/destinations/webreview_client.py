"""Built-in WebReview client (replaces the archived external `webreview` package).

Uses stdlib `http.client` (with per-thread TLS keep-alive connection reuse),
`concurrent.futures.ThreadPoolExecutor`, and Grow's native progress bar.
"""

import base64
import hashlib
import http.client
import json
import logging
import mimetypes
import os
import random
import ssl
import threading
import time
import traceback
import urllib.parse
from concurrent import futures

import httplib2
from googleapiclient import discovery, errors
from oauth2client import client, service_account, tools
from oauth2client import file as oauth_file
from protorpc import message_types, messages, protojson

from grow.common import oauth as grow_oauth
from grow.common import progressbar_non as progressbar

# Google API details for a native/installed application for API project grow-prod.
CLIENT_ID = os.getenv(
    'GROW_OAUTH_CLIENT_ID',
    '578372381550-jfl3hdlf1q5rgib94pqsctv1kgkflu1a.apps.googleusercontent.com',
)
CLIENT_SECRET = os.getenv(
    'GROW_OAUTH_CLIENT_SECRET',
    'XQKqbwTg88XVpaBNRcm_tYLf',  # Not so secret for installed apps.
)
OAUTH_SCOPES = [
    'https://www.googleapis.com/auth/plus.me',
    'https://www.googleapis.com/auth/userinfo.email',
]
APPENGINE_SERVER_PREFIXES = ('Development/', 'Google App Engine/')
IS_APPENGINE = os.getenv('SERVER_SOFTWARE', '').startswith(APPENGINE_SERVER_PREFIXES)

try:
    from oauth2client.contrib import appengine
except ImportError:
    appengine = None

DEFAULT_STORAGE_KEY = 'WebReview Client'
DEFAULT_HTTP_TIMEOUT = 60
MAX_RETRIES = 3
RETRYABLE_STATUS_CODES = frozenset({429, 502, 503, 504})
_CLEARED_AUTH_KEYS = {}


class Error(Exception):
    """Base error for WebReview client."""


class Verb:
    GET = 'GET'
    PUT = 'PUT'
    DELETE = 'DELETE'


class AuthorMessage(messages.Message):
    name = messages.StringField(1)
    email = messages.StringField(2)


class CommitMessage(messages.Message):
    sha = messages.StringField(1)
    author = messages.MessageField(AuthorMessage, 2)
    date = message_types.DateTimeField(3)
    message = messages.StringField(4)
    has_unstaged_changes = messages.BooleanField(5)
    branch = messages.StringField(6)


def batch(items, size):
    """Batches a list into sub-lists of at most `size` items."""
    return [items[x : x + size] for x in range(0, len(items), size)]


def _sanitize_storage_component(value):
    """Sanitize a filename component while preserving legacy spaces/punctuation."""
    value = str(value or 'default').replace('/', '_').replace('\\', '_').replace('\x00', '')
    if value in ('', '.', '..') or '..' in value:
        raise ValueError(f'Invalid storage identifier: {value!r}')
    return value


def get_storage(key, username):
    """Returns the Storage class compatible with the current environment."""
    if IS_APPENGINE and appengine:
        return appengine.StorageByKeyName(appengine.CredentialsModel, username, 'credentials')
    safe_key = _sanitize_storage_component(key)
    safe_username = _sanitize_storage_component(username)
    dir_name = os.path.expanduser('~/.config/webreview')
    file_name = os.path.join(dir_name, f'{safe_key}_{safe_username}')
    os.makedirs(dir_name, mode=0o700, exist_ok=True)
    return oauth_file.Storage(file_name)


class HttpWithApiKey(httplib2.Http):
    """httplib2.Http subclass that attaches WebReview-Api-Key only to the target host."""

    def __init__(self, *args, **kwargs):
        self.api_key = kwargs.pop('api_key', None)
        self.allowed_host = kwargs.pop('allowed_host', None)
        kwargs.setdefault('timeout', DEFAULT_HTTP_TIMEOUT)
        super().__init__(*args, **kwargs)

    def _request(
        self,
        conn,
        host,
        absolute_uri,
        request_uri,
        method,
        body,
        headers,
        redirections,
        cachekey,
    ):
        headers = dict(headers) if headers is not None else {}
        if self.api_key is not None:
            if self.allowed_host is None or host.lower() == self.allowed_host.lower():
                headers['WebReview-Api-Key'] = self.api_key
            else:
                headers.pop('WebReview-Api-Key', None)
        return super()._request(
            conn,
            host,
            absolute_uri,
            request_uri,
            method,
            body,
            headers,
            redirections,
            cachekey,
        )


class RpcError(Error):
    def __init__(self, status, message=None, data=None, tb=None):
        self.status = status
        if isinstance(data, dict) and 'error_message' in data:
            self.message = data['error_message']
        else:
            self.message = message
        self.data = data
        self.tb = tb

    def __repr__(self):
        return f'{self.status}: {self.message}'

    def __str__(self):
        return f'{self.status}: {self.message}'

    def __getitem__(self, name):
        return self.data[name]


class WebReviewRpcError(RpcError):
    pass


class GoogleStorageRpcError(RpcError, OSError):
    pass


class RenderedDocStub:
    """Stub to simulate a rendered document."""

    def __init__(self, path=None, content=None):
        self.path = path
        self.content = content

    def read(self):
        return self.content

    def write(self, content):
        self.content = content
        return self.content


class _ThreadLocalConnectionPool:
    """Per-thread HTTP/HTTPS keep-alive connection cache for GCS signed requests."""

    def __init__(self, timeout=DEFAULT_HTTP_TIMEOUT):
        self._timeout = timeout
        self._ssl_context = ssl.create_default_context()
        self._local = threading.local()

    def _get_cache(self):
        cache = getattr(self._local, 'conns', None)
        if cache is None:
            cache = {}
            self._local.conns = cache
        return cache

    def get(self, scheme, netloc):
        cache = self._get_cache()
        key = (scheme, netloc)
        conn = cache.get(key)
        if conn is None:
            if scheme == 'https':
                conn = http.client.HTTPSConnection(
                    netloc, timeout=self._timeout, context=self._ssl_context
                )
            elif scheme == 'http':
                conn = http.client.HTTPConnection(netloc, timeout=self._timeout)
            else:
                raise ValueError(f'Unsupported URL scheme: {scheme!r}')
            cache[key] = conn
        return conn

    def discard(self, scheme, netloc):
        cache = self._get_cache()
        conn = cache.pop((scheme, netloc), None)
        if conn is not None:
            try:
                conn.close()
            except Exception:
                pass


_GCS_CONN_POOL = _ThreadLocalConnectionPool()


class GoogleStorageSigner:
    @staticmethod
    def _to_bytes(content):
        if content is None:
            return b''
        if isinstance(content, bytes):
            return content
        if isinstance(content, bytearray):
            return bytes(content)
        if isinstance(content, str):
            return content.encode('utf-8')
        return bytes(content)

    @staticmethod
    def create_unsigned_request(verb, path, content=None):
        req = {
            'path': urllib.parse.quote(path),
            'verb': verb,
        }
        if verb == Verb.PUT:
            if path.endswith('/'):
                mimetype = 'text/html'
            else:
                mimetype = mimetypes.guess_type(path)[0] or 'application/octet-stream'
            content_bytes = GoogleStorageSigner._to_bytes(content)
            md5_digest = base64.b64encode(hashlib.md5(content_bytes).digest()).decode('utf-8')
            req['headers'] = {
                'content_length': str(len(content_bytes)),
                'content_md5': md5_digest,
                'content_type': mimetype,
            }
        return req

    def create_sign_requests_request(self, verb, fileset, paths_to_rendered_doc):
        unsigned_requests = [
            self.create_unsigned_request(verb, path, rendered_doc.read())
            for path, rendered_doc in paths_to_rendered_doc.items()
        ]
        return {
            'fileset': fileset,
            'unsigned_requests': unsigned_requests,
        }

    @staticmethod
    def execute_signed_request(signed_request, content=None, retry=0, timeout=DEFAULT_HTTP_TIMEOUT):
        req = signed_request
        verb = req['verb']
        if verb not in (Verb.PUT, Verb.GET, Verb.DELETE):
            raise ValueError(f'Unsupported HTTP verb: {verb!r}')

        parsed = urllib.parse.urlsplit(req['url'])
        if parsed.scheme not in ('http', 'https') or not parsed.netloc:
            raise ValueError(f'Invalid signed request URL: {req["url"]!r}')

        query_params = urllib.parse.parse_qsl(parsed.query, keep_blank_values=True)
        query_params.extend(
            [
                ('GoogleAccessId', req['params']['google_access_id']),
                ('Signature', req['params']['signature']),
                ('Expires', str(req['params']['expires'])),
            ]
        )
        request_target = parsed.path or '/'
        encoded_query = urllib.parse.urlencode(query_params)
        if encoded_query:
            request_target = f'{request_target}?{encoded_query}'

        headers = {'Connection': 'keep-alive'}
        body = None
        if verb == Verb.PUT:
            body = GoogleStorageSigner._to_bytes(content)
            headers['Content-Type'] = req['headers']['content_type']
            headers['Content-MD5'] = req['headers']['content_md5']
            headers['Content-Length'] = req['headers']['content_length']

        pool = (
            _GCS_CONN_POOL
            if timeout == DEFAULT_HTTP_TIMEOUT
            else _ThreadLocalConnectionPool(timeout=timeout)
        )

        last_err = None
        for attempt in range(retry, MAX_RETRIES + 1):
            conn = pool.get(parsed.scheme, parsed.netloc)
            try:
                conn.request(verb, request_target, body=body, headers=headers)
                resp = conn.getresponse()
                resp_body = resp.read()
                status = resp.status
            except (
                http.client.HTTPException,
                OSError,
            ) as err:
                pool.discard(parsed.scheme, parsed.netloc)
                last_err = err
                if attempt < MAX_RETRIES:
                    time.sleep(0.25 * (2**attempt) + random.uniform(0, 0.1))
                    continue
                raise GoogleStorageRpcError(0, message=str(err)) from err

            if status in RETRYABLE_STATUS_CODES and attempt < MAX_RETRIES:
                pool.discard(parsed.scheme, parsed.netloc)
                time.sleep(0.5 * (2**attempt) + random.uniform(0, 0.2))
                continue

            if not (200 <= status < 205):
                raise GoogleStorageRpcError(status, message=resp_body)
            return resp_body

        raise GoogleStorageRpcError(0, message=str(last_err))


class WebReview:
    _pool_size = 10

    def __init__(
        self,
        project=None,
        name=None,
        commit=None,
        host=None,
        secure=False,
        username='default',
        api='webreview',
        version='v0',
        api_key=None,
    ):
        if not project or '/' not in project:
            raise ValueError('Project must be in format: <owner>/<project>')
        parts = project.split('/', 1)
        if not parts[0] or not parts[1]:
            raise ValueError('Project must be in format: <owner>/<project>')
        self.owner, self.project = parts
        self.name = name
        self.gs = GoogleStorageSigner()
        self.lock = threading.Lock()
        self.commit = commit
        self._host = host
        root = f'{"https" if secure else "http"}://{host}/_ah/api'
        self.api_key = api_key
        self._username = username
        self._api = api
        self._version = version
        self._url = f'{root}/discovery/v1/apis/{api}/{version}/rest'
        self._service = None
        self._discovery_doc = None
        self._credentials = None

    @property
    def fileset(self):
        commit = None
        if self.commit:
            commit = json.loads(protojson.encode_message(self.commit))
        return {
            'name': self.name.lower() if self.name else '',
            'commit': commit,
            'project': {
                'nickname': self.project.lower() if self.project else '',
                'owner': {
                    'nickname': self.owner.lower() if self.owner else '',
                },
            },
        }

    def _build_http(self, credentials=None):
        http = HttpWithApiKey(api_key=self.api_key, allowed_host=self._host)
        if self.api_key is None and credentials is not None:
            credentials.authorize(http)
            if credentials.access_token_expired:
                credentials.refresh(http)
        return http

    def get_service(self, username=None, reauth=False):
        if username is None:
            username = self._username
        credentials = None
        if self.api_key is None:
            if reauth or self._credentials is None:
                self._credentials = WebReview.get_credentials(username=username, reauth=reauth)
            credentials = self._credentials
        http = self._build_http(credentials)
        if self._discovery_doc is not None:
            return discovery.build_from_document(self._discovery_doc, http=http)
        service = discovery.build(
            self._api,
            self._version,
            discoveryServiceUrl=self._url,
            http=http,
        )
        # Cache discovery JSON so parallel batch threads don't re-fetch it.
        if hasattr(service, '_resourceDesc'):
            self._discovery_doc = json.dumps(service._resourceDesc)
        return service

    def login(self, username='default', reauth=False):
        self._username = username
        self._credentials = None
        self._service = self.get_service(username=username, reauth=reauth)

    @property
    def service(self):
        if self._service is not None:
            return self._service
        self._service = self.get_service()
        return self._service

    @staticmethod
    def get_credentials(username, reauth=False):
        if os.getenv('CLEAR_AUTH') and username not in _CLEARED_AUTH_KEYS:
            WebReview.clear_credentials(username)

        key_file = os.getenv('AUTH_KEY_FILE')
        if not key_file and os.path.exists(grow_oauth.DEFAULT_AUTH_KEY_FILE):
            key_file = grow_oauth.DEFAULT_AUTH_KEY_FILE
        if key_file:
            key_file = os.path.expanduser(key_file)
            return service_account.ServiceAccountCredentials.from_json_keyfile_name(
                key_file, OAUTH_SCOPES
            )

        storage = get_storage(DEFAULT_STORAGE_KEY, username)
        if not reauth:
            credentials = storage.get()
            if credentials and not credentials.invalid:
                return credentials

        if os.getenv('NO_INTERACTIVE_AUTH'):
            raise RuntimeError(
                'Non-interactive OAuth requested without a service account key.\n'
                f'{grow_oauth.OOB_GUIDANCE_MESSAGE}'
            )

        port = grow_oauth._find_available_port()
        flags, _ = tools.argparser.parse_known_args(['--auth_host_port', str(port)])
        flow = client.OAuth2WebServerFlow(
            CLIENT_ID,
            CLIENT_SECRET,
            OAUTH_SCOPES,
            redirect_uri=f'http://localhost:{port}/',
        )
        try:
            credentials = tools.run_flow(flow, storage, flags)
        except client.HttpAccessTokenRefreshError as err:
            raise client.HttpAccessTokenRefreshError(
                f'{err}\n\n{grow_oauth.OOB_GUIDANCE_MESSAGE}'
            ) from err
        except SystemExit as err:
            raise RuntimeError(
                f'OAuth authentication failed ({err}).\n\n{grow_oauth.OOB_GUIDANCE_MESSAGE}'
            ) from err
        # Restrict credential file permissions where supported.
        storage_path = getattr(storage, '_filename', None)
        if storage_path and os.path.exists(storage_path):
            try:
                os.chmod(storage_path, 0o600)
            except OSError:
                pass
        # run_flow changes the logging level, so change it back.
        logging.getLogger().setLevel(logging.INFO)
        return credentials

    @staticmethod
    def clear_credentials(username):
        storage = get_storage(DEFAULT_STORAGE_KEY, username)
        storage.delete()
        _CLEARED_AUTH_KEYS[username] = True

    def upload_dir(self, build_dir):
        paths_to_rendered_doc = WebReview._get_paths_to_rendered_doc_from_dir(build_dir)
        return self.write(paths_to_rendered_doc)

    def get_signed_requests(self, verb, paths_to_rendered_doc):
        # Batch request-signing calls into groups of 200 to avoid server deadlines.
        items_to_batch = list(paths_to_rendered_doc.items())
        batched_items = batch(items_to_batch, 200)
        if not batched_items:
            return []

        # Ensure credentials & discovery doc are loaded once before fanning out.
        if self._service is None:
            _ = self.service

        signed_requests = []
        error_objs = []

        batch_count = len(batched_items)
        bar = None
        if batch_count > 2:
            widgets = [
                progressbar.FormatLabel(f'Starting: %(value)d/{batch_count} (in %(elapsed)s)')
            ]
            bar = progressbar.ProgressBar(widgets=widgets, maxval=batch_count)
            bar.start()

        def _execute_request_signing_request(item):
            try:
                service = self.get_service()
                batched_paths_to_contents = dict(item)
                req = self.gs.create_sign_requests_request(
                    verb, self.fileset, batched_paths_to_contents
                )
                try:
                    resp = service.sign_requests(body=req).execute()
                except errors.HttpError as e:
                    with self.lock:
                        error_objs.append((e.resp.status, e._get_reason().strip(), None))
                    return
                with self.lock:
                    if bar:
                        bar.update(bar.value + 1)
                    signed_requests.extend(resp['signed_requests'])
            except Exception as err:
                tb = traceback.format_tb(err.__traceback__)
                with self.lock:
                    error_objs.append(('Error creating signed request', str(err), tb))

        max_workers = min(self._pool_size, batch_count)
        if max_workers == 1:
            _execute_request_signing_request(batched_items[0])
        else:
            with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                list(executor.map(_execute_request_signing_request, batched_items))

        if error_objs:
            status, reason, tb = error_objs[0]
            raise WebReviewRpcError(status, reason, tb=tb)
        if bar:
            bar.finish()
        return signed_requests

    def delete(self, paths):
        paths_to_rendered_doc = {path: RenderedDocStub() for path in paths}
        signed_requests = self.get_signed_requests(Verb.DELETE, paths_to_rendered_doc)
        return self._execute_signed_requests(signed_requests, paths_to_rendered_doc)

    def read(self, paths):
        paths_to_rendered_doc = {path: RenderedDocStub() for path in paths}
        signed_requests = self.get_signed_requests(Verb.GET, paths_to_rendered_doc)
        return self._execute_signed_requests(signed_requests, paths_to_rendered_doc)

    def write(self, paths_to_rendered_doc):
        signed_requests = self.get_signed_requests(Verb.PUT, paths_to_rendered_doc)
        return self._execute_signed_requests(signed_requests, paths_to_rendered_doc)

    def finalize(self):
        try:
            req = {'fileset': self.fileset}
            return self.service.finalize(body=req).execute()
        except errors.HttpError as e:
            raise WebReviewRpcError(e.resp.status, e._get_reason().strip()) from e

    def _execute(self, req, path, content, bar, resps, error_map):
        error = None
        resp = None
        try:
            resp = self.gs.execute_signed_request(req, content)
        except Exception as err:
            error = err
        with self.lock:
            if resp is not None:
                resps[path] = resp
            if error is not None:
                error_map[path] = error
            if bar is not None:
                bar.update(bar.value + 1)

    def _execute_signed_requests(self, signed_requests, paths_to_rendered_doc):
        if not signed_requests:
            raise ValueError('No requests to sign.')
        resps = {}
        error_map = {}
        num_files = len(signed_requests)

        def _prepare(req):
            path = req['path']
            path_raw = urllib.parse.unquote(path)
            content = paths_to_rendered_doc[path_raw].read()
            if isinstance(content, str):
                content = content.encode('utf-8')
            return req, path, content

        if num_files > 1:
            widgets = [progressbar.FormatLabel(f'Working: %(value)d/{num_files} (in %(elapsed)s)')]
            bar = progressbar.ProgressBar(widgets=widgets, maxval=num_files)
            bar.start()
            max_workers = min(self._pool_size, num_files)
            with futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
                tasks = [
                    executor.submit(self._execute, req, path, content, bar, resps, error_map)
                    for req, path, content in (_prepare(r) for r in signed_requests)
                ]
                for task in tasks:
                    task.result()
            bar.finish()
        else:
            req, path, content = _prepare(signed_requests[0])
            self._execute(req, path, content, None, resps, error_map)
        return resps, error_map

    @classmethod
    def _get_paths_to_rendered_doc_from_dir(cls, build_dir):
        paths_to_rendered_doc = {}
        for pre, _, files in os.walk(build_dir):
            for f in files:
                abs_path = os.path.join(pre, f)
                rel_path = os.path.relpath(abs_path, build_dir).replace(os.sep, '/')
                if not rel_path.startswith('/'):
                    rel_path = f'/{rel_path}'
                with open(abs_path, 'rb') as fp:
                    content = fp.read()
                paths_to_rendered_doc[rel_path] = RenderedDocStub(content=content)
        return paths_to_rendered_doc
