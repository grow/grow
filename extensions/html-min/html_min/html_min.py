"""HTML minification extension for Grow sites (stdlib-only, zero 3P deps)."""

import html
import re
from html.parser import HTMLParser

from grow import extensions
from grow.documents import document
from grow.extensions import hooks

_VOID_TAGS = frozenset(
    {
        'area',
        'base',
        'br',
        'col',
        'embed',
        'hr',
        'img',
        'input',
        'link',
        'meta',
        'param',
        'source',
        'track',
        'wbr',
    }
)

_DEFAULT_PRE_TAGS = ('pre', 'textarea', 'script', 'style', 'code')
_BOOLEAN_ATTRS = frozenset(
    {
        'allowfullscreen',
        'async',
        'autofocus',
        'autoplay',
        'checked',
        'controls',
        'default',
        'defer',
        'disabled',
        'formnovalidate',
        'hidden',
        'ismap',
        'itemscope',
        'loop',
        'multiple',
        'muted',
        'nomodule',
        'novalidate',
        'open',
        'playsinline',
        'readonly',
        'required',
        'reversed',
        'selected',
    }
)
_UNQUOTED_SAFE_RE = re.compile(r'^[A-Za-z0-9._:-]+$')
_WHITESPACE_RE = re.compile(r'\s+')


class _MinifyingHTMLParser(HTMLParser):
    def __init__(
        self,
        *,
        remove_comments=False,
        remove_empty_space=False,
        remove_all_empty_space=False,
        reduce_empty_attributes=True,
        reduce_boolean_attributes=False,
        remove_optional_attribute_quotes=False,
        keep_pre=False,
        pre_tags=_DEFAULT_PRE_TAGS,
        pre_attr='pre',
    ):
        super().__init__(convert_charrefs=False)
        self.remove_comments = remove_comments
        self.remove_empty_space = remove_empty_space
        self.remove_all_empty_space = remove_all_empty_space
        self.reduce_empty_attributes = reduce_empty_attributes
        self.reduce_boolean_attributes = reduce_boolean_attributes
        self.remove_optional_attribute_quotes = remove_optional_attribute_quotes
        self.keep_pre = keep_pre
        self.pre_tags = frozenset(t.lower() for t in pre_tags)
        self.pre_attr = pre_attr
        self._pre_depth = 0
        self._pre_attr_depths = []
        self._out = []

    def _in_pre(self):
        return self._pre_depth > 0 or bool(self._pre_attr_depths)

    def _format_attrs(self, attrs):
        parts = []
        has_pre_attr = False
        for name, value in attrs:
            if self.pre_attr and name == self.pre_attr:
                has_pre_attr = True
                if not self.keep_pre:
                    continue
            if (
                value is None
                or self.reduce_boolean_attributes
                and name.lower() in _BOOLEAN_ATTRS
                or self.reduce_empty_attributes
                and value == ''
            ):
                parts.append(name)
            else:
                escaped = html.escape(value, quote=True)
                if self.remove_optional_attribute_quotes and _UNQUOTED_SAFE_RE.match(value):
                    parts.append(f'{name}={escaped}')
                else:
                    parts.append(f'{name}="{escaped}"')
        return (' ' + ' '.join(parts)) if parts else '', has_pre_attr

    def handle_decl(self, decl):
        self._out.append(f'<!{decl}>')

    def handle_pi(self, data):
        self._out.append(f'<?{data}>')

    def handle_comment(self, data):
        if self.remove_comments and not data.startswith('['):
            return
        self._out.append(f'<!--{data}-->')

    def handle_starttag(self, tag, attrs):
        lower = tag.lower()
        attr_str, has_pre_attr = self._format_attrs(attrs)
        self._out.append(f'<{tag}{attr_str}>')
        if lower not in _VOID_TAGS:
            if lower in self.pre_tags:
                self._pre_depth += 1
            if has_pre_attr:
                self._pre_attr_depths.append(lower)

    def handle_startendtag(self, tag, attrs):
        attr_str, _ = self._format_attrs(attrs)
        if tag.lower() in _VOID_TAGS:
            self._out.append(f'<{tag}{attr_str}>')
        else:
            self._out.append(f'<{tag}{attr_str}/>')

    def handle_endtag(self, tag):
        lower = tag.lower()
        if lower in self.pre_tags and self._pre_depth > 0:
            self._pre_depth -= 1
        if self._pre_attr_depths and self._pre_attr_depths[-1] == lower:
            self._pre_attr_depths.pop()
        self._out.append(f'</{tag}>')

    def handle_data(self, data):
        if self._in_pre():
            self._out.append(data)
            return
        if self.remove_all_empty_space and data.strip() == '':
            return
        if self.remove_empty_space and data.strip() == '':
            return
        self._out.append(_WHITESPACE_RE.sub(' ', data))

    def handle_entityref(self, name):
        self._out.append(f'&{name};')

    def handle_charref(self, name):
        self._out.append(f'&#{name};')

    def get_html(self):
        return ''.join(self._out).strip()


def minify_html(content, **options):
    """Minifies an HTML string using stdlib HTMLParser.

    Accepts the same keyword options as ``htmlmin.minify`` for backwards
    compatibility.
    """
    if not content:
        return content
    supported = {
        'remove_comments',
        'remove_empty_space',
        'remove_all_empty_space',
        'reduce_empty_attributes',
        'reduce_boolean_attributes',
        'remove_optional_attribute_quotes',
        'keep_pre',
        'pre_tags',
        'pre_attr',
    }
    filtered = {k: v for k, v in options.items() if k in supported}
    parser = _MinifyingHTMLParser(**filtered)
    parser.feed(content)
    parser.close()
    return parser.get_html()


class HtmlMinPostRenderHook(hooks.PostRenderHook):
    """Handle the post-render hook."""

    def should_trigger(self, previous_result, *_args, **_kwargs):
        """Determine if the hook should trigger."""
        return self.extension.config.get('enabled', True)

    def trigger(self, previous_result, doc, raw_content, *_args, **_kwargs):
        """Execute post-render modification."""
        if not isinstance(doc, document.Document) or not doc.view.endswith('.html'):
            return previous_result
        content = previous_result if previous_result else raw_content
        return minify_html(content, **self.extension.config.get('options', {}))


class HtmlMinExtension(extensions.BaseExtension):
    """HTML minification extension."""

    @property
    def available_hooks(self):
        """Returns the available hook classes."""
        return [HtmlMinPostRenderHook]
