"""Security and functional tests for ext-cloud-images backend."""

import io
import json
import types
import urllib.error

import main
import pytest


def _call_wsgi(path='/', query_string='', method='GET', headers=None):
    environ = {
        'REQUEST_METHOD': method,
        'PATH_INFO': path,
        'QUERY_STRING': query_string,
        'HTTP_USER_AGENT': 'grow-ext-google-cloud-images/2.0',
    }
    for key, value in (headers or {}).items():
        environ[f'HTTP_{key.upper().replace("-", "_")}'] = value

    captured = {}

    def start_response(status, response_headers):
        captured['status'] = status
        captured['headers'] = dict(response_headers)

    body = b''.join(main.wsgi_app(environ, start_response))
    return captured['status'], captured['headers'], body


class _FakeImagesError(Exception):
    pass


class _FakeAccessDeniedError(_FakeImagesError):
    pass


class _FakeObjectNotFoundError(_FakeImagesError):
    pass


class _FakeTransformationError(_FakeImagesError):
    pass


class _FakeBadImageError(_FakeImagesError):
    pass


class _FakeImage:
    def __init__(self, image_data):
        self.width = 640
        self.height = 480


def _install_fake_appengine(monkeypatch, serving_url='https://lh3.googleusercontent.com/abc'):
    calls = {'get_serving_url': [], 'delete_serving_url': [], 'create_gs_key': []}

    fake_images = types.SimpleNamespace(
        Error=_FakeImagesError,
        AccessDeniedError=_FakeAccessDeniedError,
        ObjectNotFoundError=_FakeObjectNotFoundError,
        TransformationError=_FakeTransformationError,
        BadImageError=_FakeBadImageError,
        Image=_FakeImage,
        get_serving_url=lambda key, secure_url=True: (
            calls['get_serving_url'].append((key, secure_url)) or serving_url
        ),
        delete_serving_url=lambda key: calls['delete_serving_url'].append(key),
    )
    fake_blobstore = types.SimpleNamespace(
        create_gs_key=lambda path: calls['create_gs_key'].append(path) or f'key:{path}',
        fetch_data=lambda key, start, end: b'fake-image-bytes',
    )
    monkeypatch.setattr(main, 'images', fake_images)
    monkeypatch.setattr(main, 'blobstore', fake_blobstore)
    return calls, fake_images


def _fake_meta(bucket='public-bucket', name='dir/photo.jpg'):
    return {
        'content_type': 'image/jpeg',
        'created': 1700000000.0,
        'etag': 'etag-123',
        'metadata': {'k': 'v'},
        'size': 12345,
    }


def test_rejects_non_get_methods():
    status, headers, _ = _call_wsgi('/public-bucket/photo.jpg', method='POST')
    assert status == '405 Method Not Allowed'
    assert 'Access-Control-Allow-Origin' not in headers
    assert headers['X-Content-Type-Options'] == 'nosniff'
    assert headers['X-Frame-Options'] == 'DENY'


def test_rejects_options_without_wildcard_cors():
    status, headers, _ = _call_wsgi('/public-bucket/photo.jpg', method='OPTIONS')
    assert status == '405 Method Not Allowed'
    assert 'Access-Control-Allow-Origin' not in headers


def test_rejects_browser_user_agent():
    status, _, body = _call_wsgi(
        '/public-bucket/photo.jpg',
        headers={'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)'},
    )
    assert status == '404 Not Found'
    assert body == b''


def test_missing_path_returns_400_without_leaking_service_account():
    status, _, body = _call_wsgi('/')
    assert status == '400 Bad Request'
    assert b'gserviceaccount.com' not in body
    assert json.loads(body)['error']


@pytest.mark.parametrize(
    'bad_path',
    [
        '/public-bucket/../private-bucket/secret.jpg',
        '/public-bucket/./secret.jpg',
        '/public-bucket/a/b/../../secret.jpg',
        '/public-bucket/secret.jpg?alt=media',
        '/public-bucket/secret.jpg#frag',
        '/public-bucket/secret%2f..%2fprivate.jpg',
        '/public-bucket/foo\\bar.jpg',
        '/INVALID_UPPERCASE/photo.jpg',
        '/a..b/photo.jpg',
        '/public-bucket/photo.html',
        '/public-bucket/photo.txt',
        '/public-bucket/',
    ],
)
def test_confused_deputy_path_attacks_blocked_before_appengine(monkeypatch, bad_path):
    calls, _ = _install_fake_appengine(monkeypatch)
    probe_calls = []
    monkeypatch.setattr(
        main,
        'fetch_public_object_metadata',
        lambda b, o: probe_calls.append((b, o)) or _fake_meta(b, o),
    )

    status, _, body = _call_wsgi(bad_path)
    assert status == '404 Not Found'
    assert body == b''
    assert probe_calls == []
    assert calls['create_gs_key'] == []
    assert calls['get_serving_url'] == []


def test_locale_injection_cannot_traverse_or_cross_buckets(monkeypatch):
    calls, _ = _install_fake_appengine(monkeypatch)
    probe_calls = []
    monkeypatch.setattr(
        main,
        'fetch_public_object_metadata',
        lambda b, o: probe_calls.append((b, o)) or _fake_meta(b, o),
    )

    # Attempt path traversal via locale parameter.
    status, _, _ = _call_wsgi(
        '/public-bucket/img@{locale}.jpg',
        query_string='locale=../../private-bucket/secret',
    )
    assert status == '404 Not Found'
    assert probe_calls == []
    assert calls['get_serving_url'] == []

    # Attempt locale placeholder in bucket name itself.
    status, _, _ = _call_wsgi('/{locale}/secret.jpg', query_string='locale=private-bucket')
    assert status == '404 Not Found'
    assert probe_calls == []
    assert calls['get_serving_url'] == []


def test_allowed_buckets_blocks_unlisted_buckets(monkeypatch):
    monkeypatch.setenv('ALLOWED_BUCKETS', 'allowed-one, allowed-two')
    calls, _ = _install_fake_appengine(monkeypatch)
    probe_calls = []
    monkeypatch.setattr(
        main,
        'fetch_public_object_metadata',
        lambda b, o: probe_calls.append((b, o)) or _fake_meta(b, o),
    )

    status, _, _ = _call_wsgi('/other-bucket/photo.jpg')
    assert status == '404 Not Found'
    assert probe_calls == []
    assert calls['get_serving_url'] == []

    status, _, body = _call_wsgi('/allowed-two/photo.jpg')
    assert status == '200 OK'
    assert json.loads(body)['url'] == 'https://lh3.googleusercontent.com/abc'


def test_private_object_never_calls_appengine_images(monkeypatch):
    calls, _ = _install_fake_appengine(monkeypatch)
    monkeypatch.setattr(main, 'fetch_public_object_metadata', lambda b, o: None)

    status, _, body = _call_wsgi('/private-bucket/secret.jpg')
    assert status == '404 Not Found'
    assert body == b''
    assert calls['create_gs_key'] == []
    assert calls['get_serving_url'] == []


def test_fetch_public_metadata_rejects_mismatched_bucket_or_name(monkeypatch):
    class _FakeResp:
        status = 200

        def __init__(self, payload):
            self._payload = json.dumps(payload).encode('utf-8')

        def read(self):
            return self._payload

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    # Mismatched name returned by upstream must be rejected.
    monkeypatch.setattr(
        main._NO_REDIRECT_OPENER,
        'open',
        lambda req, timeout=10: _FakeResp({'bucket': 'other-bucket', 'name': 'photo.jpg'}),
    )
    assert main.fetch_public_object_metadata('my-bucket', 'photo.jpg') is None

    # Redirect / HTTP error must be rejected.
    def _raise_redirect(req, timeout=10):
        raise urllib.error.HTTPError(req.full_url, 302, 'Found', {}, io.BytesIO())

    monkeypatch.setattr(main._NO_REDIRECT_OPENER, 'open', _raise_redirect)
    assert main.fetch_public_object_metadata('my-bucket', 'photo.jpg') is None


def test_api_key_authentication(monkeypatch):
    monkeypatch.setenv('API_KEY', 'super-secret-token')
    _install_fake_appengine(monkeypatch)
    monkeypatch.setattr(main, 'fetch_public_object_metadata', lambda b, o: _fake_meta(b, o))

    # Missing token -> 401
    status, _, _ = _call_wsgi('/public-bucket/photo.jpg')
    assert status == '401 Unauthorized'

    # Wrong token -> 401
    status, _, _ = _call_wsgi(
        '/public-bucket/photo.jpg',
        headers={'Authorization': 'Bearer wrong-token'},
    )
    assert status == '401 Unauthorized'

    # Valid Bearer token -> 200
    status, _, _ = _call_wsgi(
        '/public-bucket/photo.jpg',
        headers={'Authorization': 'Bearer super-secret-token'},
    )
    assert status == '200 OK'

    # Valid X-API-Key token -> 200
    status, _, _ = _call_wsgi(
        '/public-bucket/photo.jpg',
        headers={'X-API-Key': 'super-secret-token'},
    )
    assert status == '200 OK'


def test_reset_cache_requires_authentication(monkeypatch):
    calls, _ = _install_fake_appengine(monkeypatch)
    monkeypatch.setattr(main, 'fetch_public_object_metadata', lambda b, o: _fake_meta(b, o))

    # Without API_KEY configured, reset_cache must be forbidden.
    monkeypatch.delenv('API_KEY', raising=False)
    status, _, _ = _call_wsgi('/public-bucket/photo.jpg', query_string='reset_cache=1')
    assert status == '403 Forbidden'
    assert calls['delete_serving_url'] == []

    # With API_KEY configured and valid token, reset_cache succeeds.
    monkeypatch.setenv('API_KEY', 'secret')
    status, _, _ = _call_wsgi(
        '/public-bucket/photo.jpg',
        query_string='reset_cache=1',
        headers={'Authorization': 'Bearer secret'},
    )
    assert status == '200 OK'
    assert calls['delete_serving_url'] == ['key:/gs/public-bucket/photo.jpg']


def test_transformation_error_does_not_copy_or_leak_sa(monkeypatch):
    _, fake_images = _install_fake_appengine(monkeypatch)
    monkeypatch.setattr(main, 'fetch_public_object_metadata', lambda b, o: _fake_meta(b, o))

    def _boom(key, secure_url=True):
        raise fake_images.TransformationError('boom')

    fake_images.get_serving_url = _boom
    status, _, body = _call_wsgi('/public-bucket/photo.jpg')
    assert status == '400 Bad Request'
    assert b'gserviceaccount.com' not in body


def test_allowed_blob_returns_direct_public_url_without_writes(monkeypatch):
    calls, _ = _install_fake_appengine(monkeypatch)
    monkeypatch.setattr(
        main,
        'fetch_public_object_metadata',
        lambda b, o: {
            'content_type': 'image/svg+xml',
            'created': 1700000000.0,
            'etag': 'etag-svg',
            'metadata': None,
            'size': 512,
        },
    )

    status, _, body = _call_wsgi('/public-bucket/icons/logo.SVG')
    assert status == '200 OK'
    data = json.loads(body)
    assert data['url'] == 'https://storage.googleapis.com/public-bucket/icons/logo.SVG'
    assert data['size'] == 512
    assert calls['get_serving_url'] == []


def test_localized_fallback_order(monkeypatch):
    _install_fake_appengine(monkeypatch)
    probed = []

    def _probe(bucket, blob):
        probed.append(blob)
        if blob == 'hero@_US.png':
            return _fake_meta(bucket, blob)
        return None

    monkeypatch.setattr(main, 'fetch_public_object_metadata', _probe)
    status, _, body = _call_wsgi(
        '/public-bucket/hero@{locale}.png',
        query_string='locale=en_US',
    )
    assert status == '200 OK'
    assert probed == ['hero@en_US.png', 'hero@_US.png']
    assert json.loads(body)['image_metadata'] == {'width': 640, 'height': 480}
