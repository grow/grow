"""Tests for xml_feed extension."""

import pytest

from xml_feed import Options, XmlFeedPreprocessHook

_SAMPLE_RSS = b"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:content="http://purl.org/rss/1.0/modules/content/">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Hello World</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 23 Nov 2026 10:00:00 +0000</pubDate>
      <description><![CDATA[<p>Intro <img src="https://example.com/a.jpg"/></p>]]></description>
    </item>
    <item>
      <title>Hello World</title>
      <link>https://example.com/2</link>
      <description>Second duplicate title</description>
    </item>
  </channel>
</rss>
"""


def test_parse_rss_articles_deduplicates_slugs_and_extracts_image():
    articles = list(XmlFeedPreprocessHook._parse_articles(_SAMPLE_RSS, Options({})))
    assert len(articles) == 2
    assert articles[0].slug == 'hello-world'
    assert articles[0].image == 'https://example.com/a.jpg'
    assert articles[0].published is not None
    assert articles[0].published.year == 2026
    # Duplicate title gets -1 suffix (previously broken due to missing used_titles.add).
    assert articles[1].slug == 'hello-world-1'
    assert articles[1].published is None


def test_rejects_xxe_doctype_and_non_http_schemes():
    evil = b'<!DOCTYPE foo [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><rss/>'
    with pytest.raises(ValueError, match='DOCTYPE/ENTITY'):
        list(XmlFeedPreprocessHook._parse_articles(evil, Options({})))

    with pytest.raises(ValueError, match='Unsupported feed URL scheme'):
        XmlFeedPreprocessHook._download_feed('file:///etc/passwd')
