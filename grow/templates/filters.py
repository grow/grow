"""Template jinja filters."""

from datetime import datetime
import copy
import hashlib
import json as json_lib
import random
import re
import jinja2
import slugify
from babel import dates as babel_dates
from babel import numbers as babel_numbers
from grow.common import json_encoder
from grow.common import urls
from grow.common import utils
from grow.templates.tags import _gettext_alias


def _deep_gettext(ctx, fields):
    if isinstance(fields, dict):
        new_dct = {}
        for key, val in fields.items():
            if isinstance(val, (dict, list, set)):
                new_dct[key] = _deep_gettext(ctx, val)
            elif isinstance(val, str):
                new_dct[key] = _gettext_alias(ctx, val)
            else:
                new_dct[key] = val
        return new_dct
    elif isinstance(fields, (list, set)):
        for i, val in enumerate(fields):
            if isinstance(val, (dict, list, set)):
                fields[i] = _deep_gettext(ctx, val)
            elif isinstance(val, str):
                fields[i] = _gettext_alias(ctx, val)
            else:
                fields[i] = val
    return fields


@jinja2.contextfilter
def deeptrans(ctx, obj):
    """Deep translate an object."""
    # Avoid issues (related to sharing the same object across locales and
    # leaking translations from one locale to another) by copying the object
    # before it's sent to deeptrans.
    new_item = copy.deepcopy(obj)
    return _deep_gettext(ctx, new_item)


@jinja2.contextfilter
def expand_partial(_ctx, partial_name):
    """Filter for expanding partial path from name of partial."""
    return '/partials/{0}/{0}.html'.format(partial_name)


@jinja2.contextfilter
def hash_value(_ctx, value, algorithm='sha'):
    """Hash the value using the algorithm."""
    value = value.encode('utf-8')

    if algorithm in ('md5',):
        return hashlib.md5(value).hexdigest()
    if algorithm in ('sha1',):
        return hashlib.sha1(value).hexdigest()
    if algorithm in ('sha224',):
        return hashlib.sha224(value).hexdigest()
    if algorithm in ('sha384',):
        return hashlib.sha384(value).hexdigest()
    if algorithm in ('sha512',):
        return hashlib.sha512(value).hexdigest()
    return hashlib.sha256(value).hexdigest()


@jinja2.contextfilter
def jsonify(_ctx, obj, *args, **kwargs):
    """Filter for JSON dumping an object."""
    return json_lib.dumps(obj, cls=json_encoder.GrowJSONEncoder, *args, **kwargs)


@jinja2.contextfilter
def markdown_filter(ctx, value):
    """Filters content through a markdown processor."""
    doc = ctx['doc']
    m_down = doc.pod.markdown
    try:
        if isinstance(value, str):
            value = value
        value = value or ''
        return m_down.convert(value)
    except UnicodeEncodeError:
        return m_down.convert(value)


@jinja2.contextfilter
def parsedatetime_filter(_ctx, date_string, string_format):
    """Filter dor parsing a datetime."""
    return datetime.strptime(date_string, string_format)


@jinja2.contextfilter
def relative_filter(ctx, path):
    """Calculates the relative path from the current url to the given url."""
    doc = ctx['doc']
    return urls.Url.create_relative_path(
        path, relative_to=doc.url.path)


@jinja2.contextfilter
def render_filter(ctx, template):
    """Creates jinja template from string and renders."""
    if isinstance(template, str):
        template = ctx.environment.from_string(template)
    return template.render(ctx)


@jinja2.contextfilter
def shuffle_filter(_ctx, seq):
    """Shuffles the list into a random order."""
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except TypeError:
        return seq

def regex_replace():
    """A regex replace filter with regex cache."""
    regex_cache = {}

    def regex_replace_filter(string, find, replace):
        """A template regex filter"""
        if find not in regex_cache:
            regex_cache[find] = re.compile(find)
        return regex_cache[find].sub(replace, string)

    return regex_replace_filter


def slug_filter(pod=None):
    """Filters string to remove url unfriendly characters."""
    use_legacy_slugify = pod and pod.is_enabled(pod.FEATURE_OLD_SLUGIFY)
    def _slug_filter(value, delimiter='-'):
        if not value:
            return value
        if use_legacy_slugify:
            return utils.slugify(value, delimiter)
        return slugify.slugify(value, separator=delimiter)
    return _slug_filter


def wrap_locale_context(func):
    """Wraps the func with the current locale."""
    @jinja2.contextfilter
    def _locale_filter(ctx, value, *args, **kwargs):
        doc = ctx['doc']
        if not kwargs.get('locale', None):
            kwargs['locale'] = str(doc.locale)
        return func(value, *args, **kwargs)
    return _locale_filter


def create_builtin_filters(env, pod=None, locale=None):
    """Filters standard for the template rendering."""
    return (
        ('currency', wrap_locale_context(babel_numbers.format_currency)),
        ('date', wrap_locale_context(babel_dates.format_date)),
        ('datetime', wrap_locale_context(babel_dates.format_datetime)),
        ('decimal', wrap_locale_context(babel_numbers.format_decimal)),
        ('deeptrans', deeptrans),
        ('expand_partial', expand_partial),
        ('hash', hash_value),
        ('jsonify', jsonify),
        ('markdown', markdown_filter),
        ('number', wrap_locale_context(babel_numbers.format_number)),
        ('percent', wrap_locale_context(babel_numbers.format_percent)),
        ('relative', relative_filter),
        ('re_replace', regex_replace()),
        ('render', render_filter),
        ('shuffle', shuffle_filter),
        ('slug', slug_filter(pod=pod)),
        ('time', wrap_locale_context(babel_dates.format_time)),
    )
