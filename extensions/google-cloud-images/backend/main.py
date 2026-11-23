"""ext-cloud-images backend.

Zero-framework WSGI service for App Engine Python 3 that generates Google Cloud
Images serving URLs for publicly readable Google Cloud Storage objects.

Security model (confused-deputy defenses):
- Optional ``API_KEY`` authentication (Bearer or ``X-API-Key`` header) using
  constant-time comparison.
- Optional ``ALLOWED_BUCKETS`` allowlist (comma-separated GCS bucket names) so
  the App Engine service account can never be induced to access buckets outside
  the configured set.
- Strict validation of bucket names, object paths, and locale strings to block
  path traversal (``..`` / ``.``), query/fragment smuggling (``?``, ``#``,
  ``%``), backslashes, and control characters.
- Anonymous public-readability verification via the unauthenticated GCS JSON
  metadata endpoint (with redirects disabled) *before* any App Engine bundled
  service API is invoked, eliminating privileged-SA existence oracles.
- Strictly read-only on GET requests: no GCS object copies or metadata
  mutations, and ``reset_cache`` (``images.delete_serving_url``) is only
  permitted for authenticated callers.
"""

import hmac
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime

try:
    from google.appengine.api import images, wrap_wsgi_app
    from google.appengine.ext import blobstore
except ImportError:  # pragma: no cover - allows importing/testing outside App Engine
    images = None
    blobstore = None
    wrap_wsgi_app = None

IMAGE_EXTENSIONS = (
    '.gif',
    '.jpeg',
    '.jpg',
    '.png',
    '.webp',
)

BLOB_EXTENSIONS = (
    '.json',
    '.mp4',
    '.svg',
    '.webm',
)

ALLOWED_EXTENSIONS = IMAGE_EXTENSIONS + BLOB_EXTENSIONS

# Timeout (in seconds) for the anonymous public-readability / metadata check.
PUBLIC_READ_CHECK_TIMEOUT = 10

# GCS bucket naming rules: 3-63 chars, lowercase letters, digits, dots, hyphens,
# underscores, starting and ending with alphanumeric.
_BUCKET_RE = re.compile(r'^[a-z0-9][a-z0-9._-]{1,61}[a-z0-9]$')
_LOCALE_RE = re.compile(r'^[A-Za-z0-9_-]{0,32}$')
_FORBIDDEN_BLOB_CHARS = frozenset('?#%\\')

_SECURITY_HEADERS = [
    ('X-Content-Type-Options', 'nosniff'),
    ('X-Frame-Options', 'DENY'),
    ('Cache-Control', 'no-store'),
]


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Prevents urllib from following HTTP 3xx redirects."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_NO_REDIRECT_OPENER = urllib.request.build_opener(_NoRedirectHandler)


def get_allowed_buckets():
    """Returns the configured bucket allowlist as a frozenset (empty = unset)."""
    raw = os.environ.get('ALLOWED_BUCKETS', '')
    return frozenset(b.strip() for b in raw.split(',') if b.strip())


def get_api_key():
    """Returns the configured API key, or empty string if unset."""
    return os.environ.get('API_KEY', '').strip()


def extract_caller_token(environ):
    """Extracts an API token from Authorization Bearer or X-API-Key headers."""
    auth = environ.get('HTTP_AUTHORIZATION', '')
    if auth.lower().startswith('bearer '):
        return auth[7:].strip()
    return environ.get('HTTP_X_API_KEY', '').strip()


def is_authenticated(environ):
    """Returns True iff API_KEY is configured and matches the caller token."""
    expected = get_api_key()
    if not expected:
        return False
    provided = extract_caller_token(environ)
    if not provided:
        return False
    return hmac.compare_digest(provided, expected)


def looks_like_browser(user_agent):
    """Returns whether a User-Agent looks like an interactive web browser.

    Defense-in-depth only (User-Agent is trivially spoofable); the real
    controls are ``ALLOWED_BUCKETS``, ``API_KEY``, and the anonymous
    public-readability check.
    """
    return 'mozilla/' in (user_agent or '').lower()


def validate_bucket_name(bucket_name):
    """Validates a GCS bucket name against GCS naming rules and allowlist."""
    if not bucket_name or '..' in bucket_name or not _BUCKET_RE.match(bucket_name):
        return False
    allowed = get_allowed_buckets()
    return not (allowed and bucket_name not in allowed)


def validate_locale(locale):
    """Validates a locale identifier so it cannot inject path characters."""
    return bool(_LOCALE_RE.match(locale or ''))


def validate_blob_name(blob_name):
    """Validates a GCS object name to prevent traversal or URL smuggling."""
    if not blob_name or len(blob_name.encode('utf-8')) > 1024:
        return False
    if blob_name.startswith('/') or blob_name.endswith('/'):
        return False
    for ch in blob_name:
        if ord(ch) < 0x20 or ord(ch) == 0x7F or ch in _FORBIDDEN_BLOB_CHARS:
            return False
    segments = blob_name.split('/')
    return all(seg not in ('', '.', '..') for seg in segments)


def split_bucket_path(path):
    """Splits a ``/bucket/object/name`` path into ``(bucket, object)`` parts."""
    parts = path.lstrip('/').split('/', 1)
    bucket_name = parts[0]
    blob_name = parts[1] if len(parts) > 1 else ''
    return bucket_name, blob_name


def candidate_blob_names(raw_blob_name, locale):
    """Generates candidate object paths for optional ``{locale}`` substitution."""
    if '{locale}' not in raw_blob_name:
        return [raw_blob_name]

    candidates = []
    if locale:
        candidates.append(raw_blob_name.replace('{locale}', locale))
        if '_' in locale:
            _, territory = locale.split('_', 1)
            if territory:
                candidates.append(raw_blob_name.replace('{locale}', f'_{territory}'))
    base = raw_blob_name.replace('@{locale}', '').replace('{locale}', '')
    if base not in candidates:
        candidates.append(base)
    return candidates


def _parse_rfc3339_timestamp(value):
    """Parses a GCS RFC 3339 ``timeCreated`` string into an epoch float."""
    if not value:
        return None
    try:
        normalized = value[:-1] + '+00:00' if value.endswith('Z') else value
        return datetime.fromisoformat(normalized).timestamp()
    except ValueError:
        return None


def fetch_public_object_metadata(bucket_name, blob_name):
    """Fetches metadata for an anonymously readable GCS object.

    Uses the unauthenticated GCS JSON metadata endpoint with redirects disabled.
    If the object does not exist or is not publicly readable, returns ``None``.
    Cross-checks the returned ``bucket`` and ``name`` fields against the
    requested ``(bucket_name, blob_name)`` to guarantee a 1-to-1 match.
    """
    quoted_bucket = urllib.parse.quote(bucket_name, safe='')
    quoted_blob = urllib.parse.quote(blob_name, safe='')
    url = f'https://storage.googleapis.com/storage/v1/b/{quoted_bucket}/o/{quoted_blob}'
    req = urllib.request.Request(url, method='GET')
    try:
        with _NO_REDIRECT_OPENER.open(req, timeout=PUBLIC_READ_CHECK_TIMEOUT) as resp:
            if resp.status != 200:
                return None
            payload = json.loads(resp.read().decode('utf-8'))
    except (urllib.error.URLError, ValueError, OSError):
        return None

    if payload.get('bucket') != bucket_name or payload.get('name') != blob_name:
        return None

    raw_size = payload.get('size')
    try:
        size = int(raw_size) if raw_size is not None else None
    except (TypeError, ValueError):
        size = None

    return {
        'content_type': payload.get('contentType'),
        'created': _parse_rfc3339_timestamp(payload.get('timeCreated')),
        'etag': payload.get('etag'),
        'metadata': payload.get('metadata'),
        'size': size,
    }


def resolve_public_object(gs_path, locale):
    """Validates input and resolves the first publicly readable GCS object.

    Returns ``(bucket_name, blob_name, metadata)`` or ``None``.
    """
    if not validate_locale(locale):
        return None

    bucket_name, raw_blob_name = split_bucket_path(gs_path)
    if '{locale}' in bucket_name or not validate_bucket_name(bucket_name):
        return None

    for blob_name in candidate_blob_names(raw_blob_name, locale):
        if not validate_blob_name(blob_name):
            continue
        if not blob_name.lower().endswith(ALLOWED_EXTENSIONS):
            continue
        metadata = fetch_public_object_metadata(bucket_name, blob_name)
        if metadata is not None:
            return bucket_name, blob_name, metadata
    return None


def _respond(start_response, status, body=b'', content_type='text/plain; charset=utf-8'):
    headers = [
        ('Content-Type', content_type),
        ('Content-Length', str(len(body))),
        *_SECURITY_HEADERS,
    ]
    start_response(status, headers)
    return [body]


def _respond_json(start_response, status, data):
    body = json.dumps(data).encode('utf-8')
    return _respond(start_response, status, body, content_type='application/json')


def wsgi_app(environ, start_response):
    """PEP 3333 WSGI application for generating Google Cloud Images URLs."""
    method = environ.get('REQUEST_METHOD', 'GET').upper()
    if method != 'GET':
        return _respond(start_response, '405 Method Not Allowed')

    if looks_like_browser(environ.get('HTTP_USER_AGENT')):
        return _respond(start_response, '404 Not Found')

    api_key_configured = bool(get_api_key())
    caller_authed = is_authenticated(environ)
    if api_key_configured and not caller_authed:
        return _respond_json(start_response, '401 Unauthorized', {'error': 'Unauthorized'})

    query = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=False)
    path_info = environ.get('PATH_INFO', '').lstrip('/')
    gs_path = (query.get('gs_path', [''])[0] or path_info).strip()
    reset_cache = bool(query.get('reset_cache', [''])[0])
    locale = query.get('locale', [''])[0]

    if not gs_path:
        return _respond_json(
            start_response,
            '400 Bad Request',
            {'error': 'Missing required GCS path: /<bucket>/<object>.ext'},
        )

    if reset_cache and not caller_authed:
        return _respond_json(
            start_response,
            '403 Forbidden',
            {'error': 'Authentication is required for reset_cache'},
        )

    resolved = resolve_public_object(gs_path, locale)
    if resolved is None:
        return _respond(start_response, '404 Not Found')

    bucket_name, blob_name, obj_meta = resolved

    if blob_name.lower().endswith(IMAGE_EXTENSIONS):
        if images is None or blobstore is None:
            return _respond_json(
                start_response,
                '500 Internal Server Error',
                {'error': 'App Engine Images API is unavailable'},
            )
        full_gs_path = f'/gs/{bucket_name}/{blob_name}'
        blob_key = blobstore.create_gs_key(full_gs_path)
        if reset_cache:
            try:
                images.delete_serving_url(blob_key)
            except images.Error:
                logging.exception('Error deleting serving URL for %s', full_gs_path)
        try:
            url = images.get_serving_url(blob_key, secure_url=True)
        except (
            images.AccessDeniedError,
            images.ObjectNotFoundError,
            images.TransformationError,
        ):
            logging.exception('Error generating serving URL for %s', full_gs_path)
            return _respond_json(
                start_response,
                '400 Bad Request',
                {'error': 'Unable to generate image serving URL for object'},
            )

        image_metadata = {}
        try:
            data = blobstore.fetch_data(blob_key, 0, 50000)
            image = images.Image(image_data=data)
            image_metadata = {
                'height': image.height,
                'width': image.width,
            }
        except images.BadImageError:
            logging.exception('Failed to inspect image dimensions for %s', full_gs_path)

        return _respond_json(
            start_response,
            '200 OK',
            {
                'content_type': obj_meta['content_type'],
                'created': obj_meta['created'],
                'etag': obj_meta['etag'],
                'image_metadata': image_metadata,
                'metadata': obj_meta['metadata'],
                'size': obj_meta['size'],
                'url': url,
            },
        )

    # Allowed non-image public blobs (.json, .mp4, .svg, .webm):
    # Return the direct public GCS URL without copying or mutating the object.
    quoted_bucket = urllib.parse.quote(bucket_name, safe='')
    quoted_blob = urllib.parse.quote(blob_name, safe='/')
    direct_url = f'https://storage.googleapis.com/{quoted_bucket}/{quoted_blob}'
    return _respond_json(
        start_response,
        '200 OK',
        {
            'content_type': obj_meta['content_type'],
            'created': obj_meta['created'],
            'etag': obj_meta['etag'],
            'image_metadata': {},
            'metadata': obj_meta['metadata'],
            'size': obj_meta['size'],
            'url': direct_url,
        },
    )


app = wrap_wsgi_app(wsgi_app) if wrap_wsgi_app is not None else wsgi_app


if __name__ == '__main__':
    from wsgiref.simple_server import make_server

    port = int(os.environ.get('PORT', '8080'))
    with make_server('127.0.0.1', port, app) as httpd:
        httpd.serve_forever()
