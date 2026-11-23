"""Tests for html_min extension."""

from html_min import HtmlMinExtension, minify_html


def test_minify_preserves_pre_and_script_and_collapses_whitespace():
    raw = """<!doctype html>
    <html>
      <body>
        <!-- a comment -->
        <p class="lead">  Hello   world  </p>
        <pre>  line 1
          line 2  </pre>
        <script>const x = "a   b";</script>
      </body>
    </html>"""
    out = minify_html(raw, remove_comments=True, remove_empty_space=True)
    assert '<!-- a comment -->' not in out
    assert '<p class="lead"> Hello world </p>' in out
    assert '<pre>  line 1\n          line 2  </pre>' in out
    assert '<script>const x = "a   b";</script>' in out


def test_minify_preserves_conditional_comments_and_entities():
    raw = '<!--[if IE]>ie<![endif]--><span>&amp;&#169;</span>'
    out = minify_html(raw, remove_comments=True)
    assert '<!--[if IE]>ie<![endif]-->' in out
    assert '&amp;&#169;' in out


def test_minify_boolean_and_optional_quotes():
    raw = '<input type="checkbox" disabled="disabled" value="">'
    out = minify_html(
        raw,
        reduce_boolean_attributes=True,
        reduce_empty_attributes=True,
        remove_optional_attribute_quotes=True,
    )
    assert out == '<input type=checkbox disabled value>'


def test_extension_exposes_post_render_hook():
    ext = HtmlMinExtension(pod=None, config={})
    assert len(ext.available_hooks) == 1
