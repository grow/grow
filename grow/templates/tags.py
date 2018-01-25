"""Template jinja tags."""

import collections as py_collections
import itertools
from datetime import datetime
import jinja2
from babel.messages import catalog as babel_catalog
from grow.collections import collection as collection_lib
from grow.common import structures
from grow.common import utils
from grow.translations import locales as locales_lib


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


@jinja2.contextfunction
def _gettext_alias(__context, *args, **kwargs):
    return __context.call(__context.resolve('gettext'), *args, **kwargs)


def _read_csv(pod, pod_path, locale):
    """Reads a csv file using a cache."""
    file_cache = pod.podcache.file_cache
    contents = file_cache.get(pod_path, locale=locale)
    if contents is None:
        contents = pod.read_csv(pod_path, locale=locale)
        file_cache.add(pod_path, contents, locale=locale)
    return contents


def _read_json(pod, pod_path):
    """Reads a json file using a cache."""
    file_cache = pod.podcache.file_cache
    contents = file_cache.get(pod_path)
    if contents is None:
        contents = pod.read_json(pod_path)
        file_cache.add(pod_path, contents)
    return contents


def _read_yaml(pod, pod_path, locale):
    """Reads a yaml file using a cache."""
    file_cache = pod.podcache.file_cache
    contents = file_cache.get(pod_path, locale)
    if contents is None:
        contents = pod.read_yaml(pod_path, locale=locale)
        file_cache.add(pod_path, contents, locale=locale)
    return contents


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
def collections(collection_paths=None, _pod=None):
    """Retrieves collections from the pod."""
    return _pod.list_collections(collection_paths)


@utils.memoize_tag
def csv(path, locale=utils.SENTINEL, _pod=None):
    """Retrieves a csv file from the pod."""
    return _read_csv(_pod, path, locale=locale)


def date(datetime_obj=None, _pod=None, **kwargs):
    """Creates a date optionally from another date."""
    _from = kwargs.get('from', None)
    if datetime_obj is None:
        datetime_obj = datetime.now()
    elif isinstance(datetime_obj, basestring) and _from is not None:
        datetime_obj = datetime.strptime(datetime_obj, _from)
    return datetime_obj


@utils.memoize_tag
def docs(collection, _pod=None, **kwargs):
    """Retrieves docs from the pod."""
    collection = _pod.get_collection(collection)
    return list(collection.list_docs(**kwargs))


@utils.memoize_tag
def get_doc(pod_path, locale=None, _pod=None):
    """Retrieves a doc from the pod."""
    return _pod.get_doc(pod_path, locale=locale)


@utils.memoize_tag
def json(path, _pod):
    """Retrieves a json file from the pod."""
    return _read_json(_pod, path)


@utils.memoize_tag
def locale_tag(code, _pod=None):
    """Parses locale from a given locale code."""
    return locales_lib.Locale.parse(code)


@utils.memoize_tag
def locales_tag(codes, _pod=None):
    """Parses locales from the given locale codes."""
    return locales_lib.Locale.parse_codes(codes)


def make_doc_gettext(doc):
    """Create a gettext function that tracks translation stats."""
    if not doc:
        return _gettext_alias

    translation_stats = doc.pod.translation_stats
    catalog = doc.pod.catalogs.get(doc.locale)

    @jinja2.contextfunction
    def gettext(__context, __string, *args, **kwargs):
        # Elegantly handle non-strings passed to gettext.
        if not isinstance(__string, basestring):
            return __string
        # Use the message from the catalog. If there is none (if `extract`
        # hasn't been run yet to create empty messages), create a stub message
        # used for tracking untranslated strings.
        message = catalog[__string] \
            or babel_catalog.Message(__string, locations=[(doc.pod_path, 0)])
        translation_stats.tick(
            message, doc.locale, doc.default_locale, location=doc.pod_path)
        return __context.call(__context.resolve('gettext'), __string, *args, **kwargs)
    return gettext


def make_gettext(func):
    """Create a gettext function that tracks translation stats."""
    @jinja2.contextfunction
    def gettext(__context, __string, **variables):
        """Gettext and do replacement."""
        value = __context.call(func, __string)
        value = value % variables
        value = utils.safe_format(value, **variables)
        if __context.eval_ctx.autoescape:
            value = jinja2.utils.Markup(value)
        return value
    return gettext


def make_ngettext(func):
    """Create a gettext function that tracks translation stats."""
    @jinja2.contextfunction
    def ngettext(__context, __singular, __plural, __num, **variables):
        """Gettext and do replacement."""
        variables.setdefault('num', __num)
        value = __context.call(func, __singular, __plural, __num)
        value = value % variables
        value = utils.safe_format(value, **variables)
        if __context.eval_ctx.autoescape:
            value = jinja2.utils.Markup(value)
        return value
    return ngettext


@utils.memoize_tag
def nav(collection=None, locale=None, _pod=None):
    """Builds a navigation object for templates."""
    collection_obj = _pod.get_collection('/content/' + collection)
    results = collection_obj.docs(order_by='order', locale=locale)
    menu = Menu()
    menu.build(results)
    return menu


@utils.memoize_tag
def static_file(path, locale=None, _pod=None):
    """Retrieves a static file from the pod."""
    return _pod.get_static(path, locale=locale)


@utils.memoize_tag
def statics(pod_path, locale=None, include_hidden=False, _pod=None):
    """Retrieves a list of statics from the pod."""
    return list(_pod.list_statics(pod_path, locale=locale, include_hidden=include_hidden))


@utils.memoize_tag
def url(pod_path, locale=None, _pod=None):
    """Retrieves a url for a given document in the pod."""
    return _pod.get_url(pod_path, locale=locale)


def wrap_locale_context(func):
    """Wraps the func with the current locale."""

    @jinja2.contextfilter
    def _locale_filter(ctx, value, *args, **kwargs):
        doc = ctx['doc']
        if not kwargs.get('locale', None):
            kwargs['locale'] = str(doc.locale)
        return func(value, *args, **kwargs)
    return _locale_filter


@utils.memoize_tag
def yaml(path, _pod, _doc=None):
    """Retrieves a yaml file from the pod."""
    locale = str(_doc.locale_safe) if _doc else None
    if '?' in path:
        path, reference = path.split('?')
        data = structures.DeepReferenceDict(_read_yaml(_pod, path, locale=locale))
        return data[reference]
    return _read_yaml(_pod, path, locale=locale)


def create_builtin_tags(pod, doc, track_dependency=None):
    """Creates standard set of tags for rendering based on the doc."""

    def _wrap(func):
        # pylint: disable=unnecessary-lambda
        return lambda *args, **kwargs: func(*args, _pod=pod, **kwargs)

    def _wrap_dependency(func):
        def _wrapper(*args, **kwargs):
            if doc and not kwargs.get('locale', None):
                # Only override the locale kwarg if it is absent. Avoid
                # replacing an explicit `locale=None` with the document's
                # current locale. The presence of a `locale=None` indicates
                # caller specifies "no locale" rather than "the current
                # document's default locale".
                if 'locale' not in kwargs:
                    kwargs['locale'] = str(doc.locale)
            included_docs = func(*args, _pod=pod, **kwargs)
            if track_dependency:
                try:
                    for included_doc in included_docs:
                        track_dependency(included_doc.pod_path)
                except TypeError:
                    # Not an interable, try it as a doc.
                    track_dependency(included_docs.pod_path)
            return included_docs
        return _wrapper

    def _wrap_dependency_path(func):
        def _wrapper(*args, **kwargs):
            if track_dependency:
                track_dependency(args[0])
            return func(*args, _pod=pod, **kwargs)
        return _wrapper

    def _wrap_doc(func):
        def _wrapper(*args, **kwargs):
            if doc:
                kwargs['_doc'] = doc
            return func(*args, **kwargs)
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
        'locale': _wrap(locale_tag),
        'locales': _wrap(locales_tag),
        'nav': _wrap(nav),
        'static': _wrap_dependency(static_file),
        'statics': _wrap_dependency(statics),
        'url': _wrap_dependency_path(url),
        'yaml': _wrap_dependency_path(_wrap_doc(yaml)),
    }


def create_builtin_globals(env, pod, locale=None):
    """Create built in global tags."""
    # Mark that we are using the newstyle gettext to avoid issues with escaping.
    env.newstyle_gettext = True
    get_gettext_func = pod.catalogs.get_gettext_translations
    gettext = make_gettext(
        lambda x: get_gettext_func(locale).ugettext(x))
    ngettext = make_ngettext(
        lambda s, p, n: get_gettext_func(locale).ungettext(s, p, n))
    return {
        'gettext': gettext,
        'ngettext': ngettext,
    }
