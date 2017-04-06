from . import collection as collection_lib
from babel import dates as babel_dates
from babel import numbers as babel_numbers
from datetime import datetime
from grow.common import utils
from grow.pods import locales as locales_lib
from grow.pods import urls
import collections
import itertools
import jinja2
import json as json_lib
import markdown
import re
import sys


def categories(collection=None, collections=None, reverse=None, order_by=None,
               locale=utils.SENTINEL, _pod=None, use_cache=False):
    if isinstance(collection, collection_lib.Collection):
        collection = collection
    elif isinstance(collection, basestring):
        collection = _pod.get_collection(collection)
    else:
        text = '{} must be a Collection instance or a collection path, found: {}.'
        raise ValueError(text.format(collection, type(collection)))
    # Collection's categories are only used for sort order.
    def sort_func(grouped_item):
        category = grouped_item[0]
        try:
            return category_list.index(category)
        except ValueError:
            return sys.maxint  # Unspecified items go to the end.
    category_list = collection.list_categories()
    docs = collection.docs(reverse=reverse, locale=locale, order_by='category')
    result = []
    for category, unsorted_docs in itertools.groupby(docs, key=lambda doc: doc.category):
        sorted_docs = sorted(unsorted_docs, key=lambda doc: doc.order)
        result.append((category, sorted_docs))
    return result


@utils.memoize_tag
def collection(collection, _pod=None):
    return _pod.get_collection(collection)


@utils.memoize_tag
def docs(collection, locale=None, order_by=None, hidden=False, recursive=True, _pod=None):
    collection = _pod.get_collection(collection)
    return collection.docs(locale=locale, order_by=order_by, include_hidden=hidden,
                           recursive=recursive)


@utils.memoize_tag
def collections(collection_paths=None, _pod=None):
    return _pod.list_collections(collection_paths)


@utils.memoize_tag
def statics(pod_path, locale=None, include_hidden=False, _pod=None):
    return list(_pod.list_statics(pod_path, locale=locale, include_hidden=include_hidden))


def markdown_filter(value):
    try:
        if isinstance(value, unicode):
            value = value.decode('utf-8')
        value = value or ''
        return markdown.markdown(value)
    except UnicodeEncodeError:
        return markdown.markdown(value)


_slug_regex = re.compile(r'[^A-Za-z0-9-._~]+')

def slug_filter(value):
    return unicode(u'-'.join(_slug_regex.split(value.lower())).strip(u'-'))


@utils.memoize_tag
def static(path, locale=None, _pod=None):
    return _pod.get_static(path, locale=locale)


class Menu(object):

    def __init__(self):
        self.items = collections.OrderedDict()

    def build(self, nodes):
        self._recursive_build(self.items, None, nodes)

    def iteritems(self):
        return self.items.iteritems()

    def _recursive_build(self, tree, parent, nodes):
        children = [n for n in nodes if n.parent == parent]
        for child in children:
            tree[child] = collections.OrderedDict()
            self._recursive_build(tree[child], child, nodes)


@utils.memoize_tag
def nav(collection=None, locale=None, _pod=None):
    collection_obj = _pod.get_collection('/content/' + collection)
    results = collection_obj.docs(order_by='order', locale=locale)
    menu = Menu()
    menu.build(results)
    return menu


@utils.memoize_tag
def breadcrumb(doc, _pod=None):
    pass


@utils.memoize_tag
def url(pod_path, locale=None, _pod=None):
    return _pod.get_url(pod_path, locale=locale)


@utils.memoize_tag
def get_doc(pod_path, locale=None, _pod=None):
    return _pod.get_doc(pod_path, locale=locale)


@jinja2.contextfilter
def render_filter(ctx, template):
    if isinstance(template, basestring):
        template = ctx.environment.from_string(template)
    return template.render(ctx)


@jinja2.contextfilter
def parsedatetime_filter(ctx, date_string, string_format):
    return datetime.strptime(date_string, string_format)


@jinja2.contextfilter
def deeptrans(ctx, obj):
    return _deep_gettext(ctx, obj)


@jinja2.contextfilter
def jsonify(ctx, obj, *args, **kwargs):
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


def _gettext_alias(__context, *args, **kwargs):
    return __context.call(__context.resolve('gettext'), *args, **kwargs)


@utils.memoize_tag
def csv(path, locale=utils.SENTINEL, _pod=None):
    return _pod.read_csv(path, locale=locale)


@utils.memoize_tag
def yaml(path, _pod):
    return _pod.read_yaml(path)


@utils.memoize_tag
def json(path, _pod):
    return _pod.read_json(path)


def date(datetime_obj=None, _pod=None, **kwargs):
    _from = kwargs.get('from', None)
    if datetime_obj is None:
        datetime_obj = datetime.now()
    elif isinstance(datetime_obj, basestring) and _from is not None:
        datetime_obj = datetime.strptime(datetime_obj, _from)
    return datetime_obj


@utils.memoize_tag
def locales(codes, _pod=None):
    return locales_lib.Locale.parse_codes(codes)


@utils.memoize_tag
def locale(code, _pod=None):
    return locales_lib.Locale.parse(code)


@jinja2.contextfilter
def relative_filter(ctx, path):
    doc = ctx['doc']
    return urls.Url.create_relative_path(
        path, relative_to=doc.url.path)


def wrap_locale_context(func):
    @jinja2.contextfilter
    def locale_filter(ctx, value, *args, **kwargs):
        doc = ctx['doc']
        if not kwargs.get('locale', None):
            kwargs['locale'] = str(doc.locale)
        return func(value, *args, **kwargs)
    return locale_filter


def create_builtin_tags(pod, doc, use_cache=False):
    def wrap(func):
        return lambda *args, **kwargs: func(
            *args, _pod=pod, use_cache=use_cache, **kwargs)

    def wrap_dependency(func, index=0):
        def wrapper(*args, **kwds):
            pod.podcache.dependency_graph.add(doc.pod_path, args[index])
            return func(*args, _pod=pod, use_cache=use_cache, **kwds)
        return wrapper

    return {
        'breadcrumb': wrap(breadcrumb),
        'categories': wrap(categories),
        'collection': wrap(collection),
        'collections': wrap(collections),
        'csv': wrap(csv),
        'date': wrap(date),
        'doc': wrap_dependency(get_doc),
        'docs': wrap_dependency(docs),
        'json': wrap(json),
        'locale': wrap(locale),
        'locales': wrap(locales),
        'nav': wrap(nav),
        'static': wrap(static),
        'statics': wrap(statics),
        'url': wrap(url),
        'yaml': wrap(yaml),
    }


def create_builtin_filters():
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
        ('slug', slug_filter),
        ('time', wrap_locale_context(babel_dates.format_time)),
        ('relative', relative_filter),
    )
