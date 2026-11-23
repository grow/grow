"""Tests for editor extension."""

import datetime

import pytest
from werkzeug.exceptions import BadRequest

from editor import EditorExtension, editor_api, handlers
from editor.api import screenshot, yaml_conversion


def test_jinja_env_works_on_jinja2_3x():
    env = handlers.create_jinja_env()
    assert env.autoescape is True


@pytest.mark.parametrize(
    'bad_path',
    [
        '',
        '/content/../../etc/passwd',
        '../secret.yaml',
        '/content/foo\\bar.yaml',
        '/content/foo\x00.yaml',
    ],
)
def test_validate_pod_path_blocks_traversal(bad_path):
    with pytest.raises(BadRequest):
        editor_api._validate_pod_path(bad_path)


def test_sanitize_filename_strips_directories():
    assert editor_api._sanitize_filename('../../evil/photo.png') == 'photo.png'
    with pytest.raises(BadRequest):
        editor_api._sanitize_filename('..')


def test_yaml_conversion_dates_and_constructors():
    fields = {
        'published': '2026-11-23',
        'updated': '2026-11-23T10:30',
        'ref': {'tag': '!g.doc', 'value': '/content/pages/home.yaml'},
    }
    out = yaml_conversion.convert_fields(fields)
    assert out['published'] == datetime.date(2026, 11, 23)
    assert out['updated'] == datetime.datetime(2026, 11, 23, 10, 30)
    assert isinstance(out['ref'], yaml_conversion.ConstructorReference)
    assert out['ref'].pod_path == '/content/pages/home.yaml'


def test_screenshot_resolution_and_hooks():
    res = screenshot.ScreenshotResolution(1280, 1600)
    assert res.resolution == '1280x1600'
    assert res.filename('hero') == 'hero-1280x1600.png'
    ext = EditorExtension(pod=None, config={})
    assert len(ext.available_hooks) == 3
