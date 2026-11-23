"""Tests for greenhouse extension and hardened backend."""

import importlib.util
import io
import json
from pathlib import Path

import pytest

from greenhouse import Error, GreenhousePreprocessor, sanitize_html

_BACKEND_PATH = Path(__file__).resolve().parent.parent / 'backend' / 'main.py'
_SPEC = importlib.util.spec_from_file_location('greenhouse_backend_main', _BACKEND_PATH)
gh_backend = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(gh_backend)


def test_sanitize_html_strips_scripts_and_javascript_urls():
    dirty = (
        '<p onclick="alert(1)">Hello <a href="javascript:evil()">bad</a> '
        '<a href="https://example.com" target="_blank">good</a></p>'
        '<script>steal()</script>'
    )
    clean = sanitize_html(dirty, ['p', 'a'], {'a': ['href']})
    assert 'script' not in clean
    assert 'steal' not in clean
    assert 'onclick' not in clean
    assert 'javascript:' not in clean
    assert '<a href="https://example.com">good</a>' in clean


def test_preprocessor_rejects_invalid_board_token():
    class _FakePod:
        root = '/tmp'
        logger = None

    pre = GreenhousePreprocessor(
        _FakePod(),
        GreenhousePreprocessor.Config(board_token='../evil', jobs_collection='/content/jobs'),
    )
    with pytest.raises(Error, match='Invalid Greenhouse board_token'):
        pre.run()


def test_backend_confused_deputy_blocks_unlisted_and_traversal_boards(monkeypatch):
    monkeypatch.setenv('ALLOWED_BOARD_TOKENS', 'acme')
    monkeypatch.setenv('GREENHOUSE_API_KEY', 'secret')

    def _post(query='', body=b''):
        captured = {}
        env = {
            'REQUEST_METHOD': 'POST',
            'PATH_INFO': '/_grow/api/submit-application',
            'QUERY_STRING': query,
            'CONTENT_TYPE': 'application/x-www-form-urlencoded',
            'CONTENT_LENGTH': str(len(body)),
            'wsgi.input': io.BytesIO(body),
        }

        def start(status, headers):
            captured['status'] = status
            captured['headers'] = dict(headers)

        resp_body = b''.join(gh_backend.app(env, start))
        return captured['status'], captured['headers'], resp_body

    status, headers, _ = _post(body=b'board_token=other-corp&job_id=123')
    assert status == '403 Forbidden'
    assert 'Access-Control-Allow-Origin' not in headers

    status, _, _ = _post(body=b'board_token=../../evil&job_id=123')
    assert status == '403 Forbidden'

    monkeypatch.setattr(gh_backend, 'submit_application', lambda *a: (200, b'{"ok":true}'))
    status, _, resp_body = _post(body=b'board_token=acme&job_id=98765')
    assert status == '200 OK'
    assert json.loads(resp_body) == {'ok': True}
