"""Hardened Python 3 WSGI backend for submitting Greenhouse job applications.

Confused-deputy protections:
- Requires ``ALLOWED_BOARD_TOKENS`` (fail-closed) so callers cannot direct the
  server's ``GREENHOUSE_API_KEY`` credentials at arbitrary Greenhouse boards.
- Strictly validates ``board_token`` and ``job_id`` to prevent path traversal.
- Explicit ``CORS_ALLOWED_ORIGINS`` allowlist (no wildcard ``*``).
- Zero web framework dependencies (stdlib WSGI + ``gunicorn``).
"""

import base64
import json
import logging
import os
import re
import urllib.error
import urllib.parse
import urllib.request

SUBMIT_URL = 'https://api.greenhouse.io/v1/boards/{board_token}/jobs/{job_id}'
SUBMIT_TIMEOUT_SECONDS = 30
_BOARD_TOKEN_RE = re.compile(r'^[A-Za-z0-9_-]+$')
_JOB_ID_RE = re.compile(r'^[0-9]+$')

_SECURITY_HEADERS = [
    ('X-Content-Type-Options', 'nosniff'),
    ('X-Frame-Options', 'DENY'),
    ('Cache-Control', 'no-store'),
]


def get_allowed_board_tokens():
    raw = os.environ.get('ALLOWED_BOARD_TOKENS', '')
    return frozenset(t.strip() for t in raw.split(',') if t.strip())


def get_allowed_origins():
    raw = os.environ.get('CORS_ALLOWED_ORIGINS', '')
    return frozenset(o.strip() for o in raw.split(',') if o.strip())


def clean_filename(name):
    base = os.path.basename(name or '')
    return ''.join(ch for ch in base if 0x20 <= ord(ch) < 0x7F and ch not in '/\\')


def validate_submission_target(board_token, job_id):
    if not board_token or not _BOARD_TOKEN_RE.match(board_token):
        return False
    if not job_id or not _JOB_ID_RE.match(str(job_id)):
        return False
    allowed = get_allowed_board_tokens()
    return bool(allowed) and board_token in allowed


def submit_application(board_token, job_id, body, content_type):
    if not validate_submission_target(board_token, job_id):
        raise ValueError('Disallowed or invalid board_token/job_id')
    api_key = os.environ.get('GREENHOUSE_API_KEY', '').strip()
    if not api_key:
        raise RuntimeError('GREENHOUSE_API_KEY is not configured')
    url = SUBMIT_URL.format(board_token=board_token, job_id=job_id)
    token = base64.b64encode(f'{api_key}:'.encode()).decode('ascii')
    headers = {
        'Authorization': f'Basic {token}',
        'Content-Type': content_type,
        'User-Agent': 'grow-ext-greenhouse-backend/2.0',
    }
    req = urllib.request.Request(url, data=body, headers=headers, method='POST')
    try:
        with urllib.request.urlopen(req, timeout=SUBMIT_TIMEOUT_SECONDS) as resp:
            return resp.status, resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read()


def _cors_headers(environ):
    origin = environ.get('HTTP_ORIGIN', '')
    if origin and origin in get_allowed_origins():
        return [
            ('Access-Control-Allow-Origin', origin),
            ('Access-Control-Allow-Methods', 'POST, OPTIONS'),
            ('Access-Control-Allow-Headers', 'origin, content-type, accept'),
            ('Vary', 'Origin'),
        ]
    return []


def _respond(start_response, status, body=b'', content_type='application/json', extra_headers=None):
    headers = [
        ('Content-Type', content_type),
        ('Content-Length', str(len(body))),
        *_SECURITY_HEADERS,
        *(extra_headers or []),
    ]
    start_response(status, headers)
    return [body]


def app(environ, start_response):
    path = environ.get('PATH_INFO', '')
    method = environ.get('REQUEST_METHOD', 'GET').upper()
    cors = _cors_headers(environ)

    if path != '/_grow/api/submit-application':
        return _respond(start_response, '404 Not Found', b'', extra_headers=cors)

    if method == 'OPTIONS':
        return _respond(start_response, '204 No Content', b'', extra_headers=cors)

    if method != 'POST':
        return _respond(start_response, '405 Method Not Allowed', b'', extra_headers=cors)

    query = urllib.parse.parse_qs(environ.get('QUERY_STRING', ''), keep_blank_values=False)
    content_type = environ.get('CONTENT_TYPE', 'application/x-www-form-urlencoded')
    try:
        content_length = int(environ.get('CONTENT_LENGTH') or 0)
    except ValueError:
        return _respond(
            start_response,
            '400 Bad Request',
            json.dumps({'error': 'Invalid Content-Length'}).encode('utf-8'),
            extra_headers=cors,
        )
    raw_body = environ['wsgi.input'].read(content_length) if content_length > 0 else b''

    board_token = query.get('board_token', [''])[0]
    job_id = query.get('job_id', [''])[0]
    if (not board_token or not job_id) and content_type.startswith(
        'application/x-www-form-urlencoded'
    ):
        form = urllib.parse.parse_qs(raw_body.decode('utf-8', errors='replace'))
        board_token = board_token or form.get('board_token', [''])[0]
        job_id = job_id or form.get('job_id', [''])[0]

    if not validate_submission_target(board_token, job_id):
        return _respond(
            start_response,
            '403 Forbidden',
            json.dumps({'error': 'Invalid or disallowed board_token/job_id'}).encode('utf-8'),
            extra_headers=cors,
        )

    try:
        status_code, resp_body = submit_application(board_token, job_id, raw_body, content_type)
    except Exception:
        logging.exception('Error submitting application for board=%s job=%s', board_token, job_id)
        return _respond(
            start_response,
            '502 Bad Gateway',
            json.dumps({'error': 'Upstream submission failed'}).encode('utf-8'),
            extra_headers=cors,
        )

    status_text = f'{status_code} OK' if 200 <= status_code < 300 else f'{status_code} Error'
    return _respond(start_response, status_text, resp_body, extra_headers=cors)
