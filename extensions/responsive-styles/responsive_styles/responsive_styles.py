"""Responsive styling with Jinja2 templates."""

import hashlib

import jinja2
import jinja2.ext

from grow import extensions
from grow.extensions import hooks

_attribute_cache = {}


def responsive_style_id(styles):
    if not styles:
        return ''
    return '-rs' + hashlib.sha1(str(styles).encode('utf-8')).hexdigest()[:4]


@jinja2.pass_context
def get_attribute_cache(ctx):
    return _attribute_cache


@jinja2.pass_context
def responsive_style_attribute(ctx, styles):
    if not styles:
        return ''
    attribute = responsive_style_id(styles)
    _attribute_cache[attribute] = styles
    return attribute


class ResponsiveStylesJinjaExtension(jinja2.ext.Extension):
    def __init__(self, env):
        super().__init__(env)
        env.globals['responsive_style_attribute'] = responsive_style_attribute
        env.globals['get_attribute_cache'] = get_attribute_cache
        env.globals['responsive_style_id'] = responsive_style_id


class ResponsiveStylesJinjaExtensionHook(hooks.JinjaExtensionHook):
    """Handle the jinja extension hook."""

    def trigger(self, previous_result, *_args, **_kwargs):
        """Add the jinja extension to the previous result."""
        previous_result.append(ResponsiveStylesJinjaExtension)
        return previous_result


class ResponsiveStylesExtension(extensions.BaseExtension):
    """Responsive styles extension."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [ResponsiveStylesJinjaExtensionHook]
