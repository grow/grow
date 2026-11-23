"""Tests for kintaro extension."""

import pytest

from kintaro import Error, GroupedEntry, kintaro, schema_name_to_partial


def test_is_document_reference_fixed():
    assert GroupedEntry.is_document_reference(
        {'collection_id': 'c', 'repo_id': 'r', 'document_id': 'd'}
    )
    assert GroupedEntry.is_document_reference(
        {'collection_id': 'c', 'repo_id': 'r', 'document_id': 'd', 'document_label': 'lbl'}
    )
    assert not GroupedEntry.is_document_reference({'title': 'Hello'})


def test_merge_data_preserves_localized_document_reference():
    base = {'title': 'Hello', 'ref': {'collection_id': 'c', 'repo_id': 'r', 'document_id': '1'}}
    loc = {'title': 'Bonjour', 'ref': {'collection_id': 'c', 'repo_id': 'r', 'document_id': '2'}}
    merged = GroupedEntry.merge_data(base, loc, 'fr_FR')
    assert merged['title@fr_FR'] == 'Bonjour'
    assert merged['ref@fr_FR']['document_id'] == '2'


def test_host_and_basename_validation():
    assert kintaro._validate_host('kintaro-content-server.appspot.com')
    with pytest.raises(Error):
        kintaro._validate_host('evil.com/path?x=1')
    with pytest.raises(Error):
        kintaro._sanitize_basename('../escape')


def test_schema_name_to_partial():
    assert schema_name_to_partial('partialHeroBanner') == '/views/partials/hero-banner.html'
    assert (
        schema_name_to_partial('partialHeroBanner', use_sub_directory=True)
        == '/views/partials/hero-banner/hero-banner.html'
    )
