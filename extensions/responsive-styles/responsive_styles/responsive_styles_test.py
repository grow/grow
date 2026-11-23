"""Tests for responsive_styles extension."""

import jinja2

from responsive_styles import (
    ResponsiveStylesExtension,
    ResponsiveStylesJinjaExtension,
    responsive_style_id,
)


def test_responsive_style_id_deterministic():
    assert responsive_style_id(None) == ''
    assert responsive_style_id('') == ''
    style_id = responsive_style_id({'mobile': {'padding': '8px'}})
    assert style_id.startswith('-rs')
    assert len(style_id) == 7
    assert style_id == responsive_style_id({'mobile': {'padding': '8px'}})


def test_jinja2_3x_extension_renders_and_caches():
    env = jinja2.Environment(extensions=[ResponsiveStylesJinjaExtension])
    tmpl = env.from_string(
        '{{ responsive_style_attribute(s) }}|{{ get_attribute_cache()[responsive_style_id(s)].mobile }}'
    )
    out = tmpl.render(s={'mobile': '10px'})
    style_id = responsive_style_id({'mobile': '10px'})
    assert out == f'{style_id}|10px'


def test_extension_hook_appends_jinja_extension():
    ext = ResponsiveStylesExtension(pod=None, config={})
    hook = ext.available_hooks[0](ext)
    result = hook.trigger([])
    assert result == [ResponsiveStylesJinjaExtension]
