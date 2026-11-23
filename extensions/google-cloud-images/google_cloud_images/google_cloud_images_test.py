"""Unit tests for the google_cloud_images Grow extension."""

import json
import urllib.error

import jinja2
import pytest

from google_cloud_images import (
    GoogleCloudImagesExtension,
    GoogleCloudImagesPreprocessor,
    GoogleImage,
    google_cloud_images,
)


class _FakeResp:
    def __init__(self, payload, status=200):
        self.status = status
        self._body = json.dumps(payload).encode('utf-8')

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_get_image_serving_data_sends_params_and_bearer_token(monkeypatch):
    captured = {}

    def _fake_urlopen(req, timeout=None):
        captured['url'] = req.full_url
        captured['auth'] = req.get_header('Authorization')
        captured['timeout'] = timeout
        return _FakeResp({'url': 'https://lh3.googleusercontent.com/xyz', 'size': 42})

    monkeypatch.setattr(google_cloud_images.urllib.request, 'urlopen', _fake_urlopen)

    data, use_cache = google_cloud_images.get_image_serving_data(
        'https://gci.example.com/',
        '/my-bucket/img.png',
        locale='en_US',
        api_key='tok-123',
    )
    assert data['url'] == 'https://lh3.googleusercontent.com/xyz'
    assert use_cache is True
    assert 'gs_path=%2Fmy-bucket%2Fimg.png' in captured['url']
    assert 'locale=en_US' in captured['url']
    assert captured['auth'] == 'Bearer tok-123'
    assert captured['timeout'] == google_cloud_images.REQUEST_TIMEOUT_SECONDS


def test_fuzzy_extension_fallback(monkeypatch):
    urls = []

    def _fake_urlopen(req, timeout=None):
        urls.append(req.full_url)
        if len(urls) == 1:
            raise urllib.error.HTTPError(req.full_url, 404, 'Not Found', {}, None)
        return _FakeResp({'url': 'https://lh3.googleusercontent.com/jpg-ok'})

    monkeypatch.setattr(google_cloud_images.urllib.request, 'urlopen', _fake_urlopen)

    data, use_cache = google_cloud_images.get_image_serving_data(
        'https://gci.example.com/',
        '/my-bucket/photo.png',
        fuzzy_extensions=True,
    )
    assert data['url'] == 'https://lh3.googleusercontent.com/jpg-ok'
    assert use_cache is True
    assert len(urls) == 2
    assert 'photo.jpg' in urls[1]


def test_placeholder_fallback_disables_cache(monkeypatch):
    urls = []

    def _fake_urlopen(req, timeout=None):
        urls.append(req.full_url)
        if len(urls) == 1:
            raise urllib.error.HTTPError(req.full_url, 404, 'Not Found', {}, None)
        return _FakeResp({'url': 'https://lh3.googleusercontent.com/placeholder'})

    monkeypatch.setattr(google_cloud_images.urllib.request, 'urlopen', _fake_urlopen)

    data, use_cache = google_cloud_images.get_image_serving_data(
        'https://gci.example.com/',
        '/my-bucket/missing.png',
        placeholders={'.png': '/my-bucket/placeholder.png'},
    )
    assert data['url'] == 'https://lh3.googleusercontent.com/placeholder'
    assert use_cache is False


def test_jinja2_extension_registers_google_image_global():
    env = jinja2.Environment(extensions=[GoogleCloudImagesExtension])
    assert 'google_image' in env.globals

    tmpl = env.from_string('{{ google_image("/b/a.png") }}')
    with pytest.raises(google_cloud_images.Error, match='Missing `doc`'):
        tmpl.render()


def test_google_image_url_options():
    img = GoogleImage(pod=None, bucket_path='/b/a.png')
    img._base_url = 'https://lh3.googleusercontent.com/abc'
    assert img.url() == 'https://lh3.googleusercontent.com/abc'
    assert img.url(['s1440', 'rw']) == 'https://lh3.googleusercontent.com/abc=s1440-rw'


def test_preprocessor_extensions_to_placeholders():
    config = GoogleCloudImagesPreprocessor.Config(
        backend='https://gci.example.com/',
        placeholders=[
            google_cloud_images.PlaceholderMessage(
                extensions=['.png', '.jpg'],
                path='/b/placeholder.png',
            )
        ],
    )

    class _FakePod:
        root = '/tmp'
        logger = None

    pre = GoogleCloudImagesPreprocessor(_FakePod(), config)
    assert pre.extensions_to_placeholders() == {
        '.png': '/b/placeholder.png',
        '.jpg': '/b/placeholder.png',
    }
