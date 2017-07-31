"""Template tags and filters."""

import collections as py_collections
from datetime import datetime
import itertools
import json as json_lib
import re
import jinja2
import markdown
import random
from babel import dates as babel_dates
from babel import numbers as babel_numbers
from grow.common import utils
from grow.pods import locales as locales_lib
from grow.pods import urls
from . import collection as collection_lib


SLUG_REGEX = re.compile(r'[^A-Za-z0-9-._~]+')


# pylint: disable=redefined-outer-name
def categories(collection=None, reverse=None, recursive=True,
               locale=utils.SENTINEL, _pod=None):
    """Retrieve catagories from the pod."""
    if isinstance(collection, collection_lib.Collection):
        collection = collection
    elif isinstance(collection, basestring):
        collection = _pod.get_collection(collection)
    else:
        text = '{} must be a Collection instance or a collection path, found: {}.'
        raise ValueError(text.format(collection, type(collection)))
    # Collection's categories are only used for sort order.
    docs = collection.docs(reverse=reverse, locale=locale, order_by='category',
                           recursive=recursive)
    result = []
    for category, unsorted_docs in itertools.groupby(docs, key=lambda doc: doc.category):
        sorted_docs = sorted(unsorted_docs, key=lambda doc: doc.order)
        result.append((category, sorted_docs))
    return result


@utils.memoize_tag
def collection(collection, _pod=None):
    """Retrieves a collection from the pod."""
    return _pod.get_collection(collection)


@utils.memoize_tag
def docs(collection, locale=None, order_by=None, hidden=False, recursive=True, _pod=None):
    """Retrieves docs from the pod."""
    collection = _pod.get_collection(collection)
    return collection.docs(locale=locale, order_by=order_by, include_hidden=hidden,
                           recursive=recursive)


@utils.memoize_tag
def collections(collection_paths=None, _pod=None):
    """Retrieves collections from the pod."""
    return _pod.list_collections(collection_paths)


@utils.memoize_tag
def statics(pod_path, locale=None, include_hidden=False, _pod=None):
    """Retrieves a list of statics from the pod."""
    return list(_pod.list_statics(pod_path, locale=locale, include_hidden=include_hidden))


def markdown_filter(value):
    """Filters content through a markdown processor."""
    try:
        if isinstance(value, unicode):
            value = value.decode('utf-8')
        value = value or ''
        return markdown.markdown(value)
    except UnicodeEncodeError:
        return markdown.markdown(value)


def slug_filter(value):
    """Filters string to remove url unfriendly characters."""
    return unicode(u'-'.join(SLUG_REGEX.split(value.lower())).strip(u'-'))


@utils.memoize_tag
def static_something(path, locale=None, _pod=None):
    """Retrieves a static file from the pod."""
    return _pod.get_static(path, locale=locale)


class Menu(object):
    """Helper class for creating navigation menus."""

    def __init__(self):
        self.items = py_collections.OrderedDict()

    def build(self, nodes):
        """Builds the menu from the set of nodes."""
        self._recursive_build(self.items, None, nodes)

    def iteritems(self):
        """Iterate through items."""
        return self.items.iteritems()

    def _recursive_build(self, tree, parent, nodes):
        children = [n for n in nodes if n.parent == parent]
        for child in children:
            tree[child] = py_collections.OrderedDict()
            self._recursive_build(tree[child], child, nodes)


@utils.memoize_tag
def nav(collection=None, locale=None, _pod=None):
    """Builds a navigation object for templates."""
    collection_obj = _pod.get_collection('/content/' + collection)
    results = collection_obj.docs(order_by='order', locale=locale)
    menu = Menu()
    menu.build(results)
    return menu


@utils.memoize_tag
def url(pod_path, locale=None, _pod=None):
    """Retrieves a url for a given document in the pod."""
    return _pod.get_url(pod_path, locale=locale)


@utils.memoize_tag
def get_doc(pod_path, locale=None, _pod=None):
    """Retrieves a doc from the pod."""
    return _pod.get_doc(pod_path, locale=locale)


@jinja2.contextfilter
def render_filter(ctx, template):
    """Creates jinja template from string and renders."""
    if isinstance(template, basestring):
        template = ctx.environment.from_string(template)
    return template.render(ctx)


@jinja2.contextfilter
def parsedatetime_filter(_ctx, date_string, string_format):
    """Filter dor parsing a datetime."""
    return datetime.strptime(date_string, string_format)


@jinja2.contextfilter
def deeptrans(ctx, obj):
    """Deep translate an object."""
    return _deep_gettext(ctx, obj)


@jinja2.contextfilter
def shuffle_filter(_ctx, seq):
    """Shuffles the list into a random order."""
    try:
        result = list(seq)
        random.shuffle(result)
        return result
    except TypeError:
        return seq


@jinja2.contextfilter
def jsonify(_ctx, obj, *args, **kwargs):
    """Filter for JSON dumping an object."""
    return json_lib.dumps(obj, *args, **kwargs)


def _deep_gettext(ctx, fields):
    if isinstance(fields, dict):
        new_dct = {}
        for key, val in fields.iteritems():
            if isinstance(val, (dict, list, set)):
                new_dct[key] = _deep_gettext(ctx, val)
            elif isinstance(val, basestring):
                new_dct[key] = _gettext_alias(ctx, val)
            else:
                new_dct[key] = val
        return new_dct
    elif isinstance(fields, (list, set)):
        for i, val in enumerate(fields):
            if isinstance(val, (dict, list, set)):
                fields[i] = _deep_gettext(ctx, val)
            elif isinstance(val, basestring):
                fields[i] = _gettext_alias(ctx, val)
            else:
                fields[i] = val
        return fields


@jinja2.contextfunction
def _gettext_alias(__context, *args, **kwargs):
    return __context.call(__context.resolve('gettext'), *args, **kwargs)


def make_doc_gettext(doc):
    translation_stats = doc.pod.translation_stats
    catalog = doc.pod.catalogs.get(doc.locale)
    gettext_trans = doc.pod.catalogs.get_gettext_translations(doc.locale)

    @jinja2.contextfunction
    def gettext(__context, __string, *args, **kwargs):
        message = catalog[__string]
        translation_stats.tick(message, doc.locale, doc.default_locale)
        return __context.call(__context.resolve('gettext'), __string, *args, **kwargs)
    return gettext


@utils.memoize_tag
def csv(path, locale=utils.SENTINEL, _pod=None):
    """Retrieves a csv file from the pod."""
    return _pod.read_csv(path, locale=locale)


@utils.memoize_tag
def yaml(path, _pod):
    """Retrieves a yaml file from the pod."""
    return _pod.read_yaml(path)


@utils.memoize_tag
def json(path, _pod):
    """Retrieves a json file from the pod."""
    return _pod.read_json(path)


def date(datetime_obj=None, _pod=None, **kwargs):
    """Creates a date optionally from another date."""
    _from = kwargs.get('from', None)
    if datetime_obj is None:
        datetime_obj = datetime.now()
    elif isinstance(datetime_obj, basestring) and _from is not None:
        datetime_obj = datetime.strptime(datetime_obj, _from)
    return datetime_obj


@utils.memoize_tag
def locales(codes, _pod=None):
    """Parses locales from the given locale codes."""
    return locales_lib.Locale.parse_codes(codes)


@utils.memoize_tag
def locale(code, _pod=None):
    """Parses locale from a given locale code."""
    return locales_lib.Locale.parse(code)


@jinja2.contextfilter
def relative_filter(ctx, path):
    """Calculates the relative path from the current url to the given url."""
    doc = ctx['doc']
    return urls.Url.create_relative_path(
        path, relative_to=doc.url.path)


def wrap_locale_context(func):
    """Wraps the func with the current locale."""

    @jinja2.contextfilter
    def _locale_filter(ctx, value, *args, **kwargs):
        doc = ctx['doc']
        if not kwargs.get('locale', None):
            kwargs['locale'] = str(doc.locale)
        return func(value, *args, **kwargs)
    return _locale_filter


def create_builtin_tags(pod, doc, use_cache=False):
    """Creates standard set of tags for rendering based on the doc."""

    def _wrap(func):
        # pylint: disable=unnecessary-lambda
        return lambda *args, **kwargs: func(
            *args, _pod=pod, use_cache=use_cache, **kwargs)

    def _wrap_dependency(func):
        def _wrapper(*args, **kwargs):
            if doc and not kwargs.get('locale', None):
                kwargs['locale'] = str(doc.locale)
            included_docs = func(
                *args, _pod=pod, use_cache=use_cache, **kwargs)
            if doc:
                try:
                    for included_doc in included_docs:
                        pod.podcache.dependency_graph.add(
                            doc.pod_path, included_doc.pod_path)
                except TypeError:
                    # Not an interable, try it as a doc.
                    pod.podcache.dependency_graph.add(
                        doc.pod_path, included_docs.pod_path)
            return included_docs
        return _wrapper

    def _wrap_dependency_path(func):
        def _wrapper(*args, **kwargs):
            if doc:
                pod.podcache.dependency_graph.add(doc.pod_path, args[0])
            return func(*args, _pod=pod, use_cache=use_cache, **kwargs)
        return _wrapper

    return {
        'categories': _wrap(categories),
        'collection': _wrap(collection),
        'collections': _wrap(collections),
        'csv': _wrap_dependency_path(csv),
        'date': _wrap(date),
        'doc': _wrap_dependency(get_doc),
        'docs': _wrap_dependency(docs),
        'json': _wrap_dependency_path(json),
        'locale': _wrap(locale),
        'locales': _wrap(locales),
        'nav': _wrap(nav),
        'static': _wrap_dependency(static_something),
        'statics': _wrap_dependency(statics),
        'url': _wrap_dependency_path(url),
        'yaml': _wrap_dependency_path(yaml),
    }


def create_builtin_filters():
    """Filters standard for the template rendering."""
    return (
        ('currency', wrap_locale_context(babel_numbers.format_currency)),
        ('date', wrap_locale_context(babel_dates.format_date)),
        ('datetime', wrap_locale_context(babel_dates.format_datetime)),
        ('decimal', wrap_locale_context(babel_numbers.format_decimal)),
        ('deeptrans', deeptrans),
        ('jsonify', jsonify),
        ('markdown', markdown_filter),
        ('number', wrap_locale_context(babel_numbers.format_number)),
        ('percent', wrap_locale_context(babel_numbers.format_percent)),
        ('render', render_filter),
        ('shuffle', shuffle_filter),
        ('slug', slug_filter),
        ('time', wrap_locale_context(babel_dates.format_time)),
        ('relative', relative_filter),
    )
