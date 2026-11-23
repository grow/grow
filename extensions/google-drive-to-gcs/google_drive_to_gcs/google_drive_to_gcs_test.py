"""Tests for google_drive_to_gcs extension."""

import jinja2
import pytest

from google_drive_to_gcs import GoogleDriveToGCSExtension, url_to_file_id


@pytest.mark.parametrize(
    ('url', 'expected'),
    [
        ('https://drive.google.com/file/d/1AbC_23-xyz/view?usp=sharing', '1AbC_23-xyz'),
        ('https://drive.google.com/file/d/1AbC_23-xyz/view', '1AbC_23-xyz'),
        ('https://drive.google.com/file/d/1AbC_23-xyz', '1AbC_23-xyz'),
        ('https://drive.google.com/open?id=1AbC_23-xyz', '1AbC_23-xyz'),
    ],
)
def test_url_to_file_id_valid(url, expected):
    assert url_to_file_id(url) == expected


@pytest.mark.parametrize(
    'bad_url',
    [
        'https://evil.example.com/file/d/123',
        'file:///etc/passwd',
        'https://drive.google.com/open?id=../../secret',
        'https://drive.google.com/file/d/',
    ],
)
def test_url_to_file_id_rejects_untrusted_or_traversal(bad_url):
    with pytest.raises(ValueError):
        url_to_file_id(bad_url)


def test_jinja2_extension_registers_global():
    env = jinja2.Environment(extensions=[GoogleDriveToGCSExtension])
    assert 'google_drive_to_gcs' in env.globals
