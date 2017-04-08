from grow.pods import errors
try:
    import cStringIO as StringIO
except ImportError:
    try:
        import StringIO
    except ImportError:
        from io import StringIO
import bs4
import csv as csv_lib
import functools
import gettext
import html2text
import imp
import json
import logging
import os
import re
import sys
import threading
import time
import translitcodec
import urllib
import yaml

# The CLoader implementation of the PyYaml loader is orders of magnitutde
# faster than the default pure Python loader. CLoader is available when
# libyaml is installed on the system.
try:
    from yaml import CLoader as yaml_Loader
except ImportError:
    logging.warning('Warning: libyaml missing, using slower yaml parser.')
    from yaml import Loader as yaml_Loader


LOCALIZED_KEY_REGEX = re.compile('(.*)@([^@]+)$')
SENTINEL = object()
SLUG_REGEX = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')


class Error(Exception):
    """Base error class."""


class UnavailableError(Error):
    """Raised when a feature is not available."""


def is_packaged_app():
    try:
        sys._MEIPASS
        return True
    except AttributeError:
        return False


def is_appengine():
    """Returns whether the environment is Google App Engine."""
    try:
        import google.appengine
        return True
    except ImportError:
        return False


def get_git():
    """Returns the git module if it is available."""
    if not is_appengine():
        import git
        return git
    raise UnavailableError('Git is not available in this environment.')


def get_grow_dir():
    if is_packaged_app():
        return os.path.join(sys._MEIPASS)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_cacerts_path():
    return os.path.join(get_grow_dir(), 'data', 'cacerts.txt')


def get_git_repo(root):
    git = get_git()
    try:
        return git.Repo(root)
    except git.exc.InvalidGitRepositoryError:
        logging.info('WARNING: No Git repository found in {}'.format(root))


def interactive_confirm(message, default=False, input_func=None):
    if input_func is None:
        input_func = lambda m: raw_input(m).lower()

    choices = 'Y/n' if default is True else 'y/N'
    message = '{} [{}]: '.format(message, choices)
    choice = input_func(message)
    if choice == 'y':
        return True
    elif choice == 'n':
        return False
    return default


def walk(node, callback, parent_key=None):
    if node is None:
        return
    for key in node:
        if isinstance(node, dict):
            item = node[key]
        else:
            item = key

        if isinstance(node, (dict)) and isinstance(item, (list, set)):
            parent_key = key

        if isinstance(item, (list, set, dict)):
            walk(item, callback, parent_key=parent_key)
        else:
            if isinstance(node, (list, set)):
                key = parent_key
            callback(item, key, node)


def validate_name(name):
    # TODO: better validation.
    if ('//' in name
        or '..' in name
        or ' ' in name):
        raise errors.BadNameError(
            'Names must be lowercase and only contain letters, numbers, '
            'backslashes, and dashes. Found: "{}"'.format(name))


class memoize(object):

    def __init__(self, func):
        self.func = func
        self.cache = {}

    def __call__(self, *args, **kwargs):
        key = (args, frozenset(kwargs.items()))
        try:
            return self.cache[key]
        except KeyError:
            value = self.func(*args, **kwargs)
            self.cache[key] = value
            return value
        except TypeError:
            return self.func(*args, **kwargs)

    def __repr__(self):
        return self.func.__doc__

    def __get__(self, obj, objtype):
        fn = functools.partial(self.__call__, obj)
        fn.reset = self._reset
        return fn

    def _reset(self):
        self.cache = {}


class cached_property(property):
    """A decorator that converts a function into a lazy property.  The
    function wrapped is called the first time to retrieve the result
    and then that calculated result is used the next time you access
    the value::

        class Foo(object):
            @cached_property
            def foo(self):
                # calculate something important here
                return 42

    The class has to have a `__dict__` in order for this property to
    work. Ported from `werkzeug`.
    """

    _sentinel = object()

    def __init__(self, func, name=None, doc=None):
        self.__name__ = name or func.__name__
        self.__module__ = func.__module__
        self.__doc__ = doc or func.__doc__
        self.func = func

    def __set__(self, obj, value):
        obj.__dict__[self.__name__] = value

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        value = obj.__dict__.get(self.__name__, self._sentinel)
        if value is self._sentinel:
            value = self.func(obj)
            obj.__dict__[self.__name__] = value
        return value


class memoize_tag(memoize):

    def __call__(self, *args, **kwargs):
        use_cache = kwargs.pop('use_cache', False)
        if use_cache is True:
            return super(memoize_tag, self).__call__(*args, **kwargs)
        return self.func(*args, **kwargs)


def every_two(l):
    return zip(l[::2], l[1::2])


def make_yaml_loader(pod, doc=None):
    class YamlLoader(yaml_Loader):

        def _construct_func(self, node, func):
            if isinstance(node, yaml.SequenceNode):
                items = []
                for i, each in enumerate(node.value):
                    items.append(func(node.value[i].value))
                return items
            return func(node.value)

        def construct_csv(self, node):
            return self._construct_func(node, pod.read_csv)

        def construct_doc(self, node):
            locale = doc._locale_kwarg if doc else None
            pod_path = doc.pod_path if doc else None
            def func(path):
                pod.podcache.dependency_graph.add(pod_path, path)
                return pod.get_doc(path, locale=locale)
            return self._construct_func(node, func)

        def construct_gettext(self, node):
            return self._construct_func(node, gettext.gettext)

        def construct_json(self, node):
            return self._construct_func(node, pod.read_json)

        def construct_static(self, node):
            locale = doc._locale_kwarg if doc else None
            func = lambda path: pod.get_static(path, locale=locale)
            return self._construct_func(node, func)

        def construct_url(self, node):
            locale = doc._locale_kwarg if doc else None
            func = lambda path: pod.get_url(path, locale=locale)
            return self._construct_func(node, func)

        def construct_yaml(self, node):
            return self._construct_func(node, pod.read_yaml)

    YamlLoader.add_constructor(u'!_', YamlLoader.construct_gettext)
    YamlLoader.add_constructor(u'!g.csv', YamlLoader.construct_csv)
    YamlLoader.add_constructor(u'!g.doc', YamlLoader.construct_doc)
    YamlLoader.add_constructor(u'!g.json', YamlLoader.construct_json)
    YamlLoader.add_constructor(u'!g.static', YamlLoader.construct_static)
    YamlLoader.add_constructor(u'!g.url', YamlLoader.construct_url)
    YamlLoader.add_constructor(u'!g.yaml', YamlLoader.construct_yaml)
    return YamlLoader


def load_yaml(*args, **kwargs):
    pod = kwargs.pop('pod', None)
    doc = kwargs.pop('doc', None)
    loader = make_yaml_loader(pod, doc=doc)
    return yaml.load(*args, Loader=loader, **kwargs) or {}


@memoize
def parse_yaml(content, pod=None):
    return load_yaml(content, pod=pod)


def dump_yaml(obj):
    return yaml.safe_dump(
        obj, allow_unicode=True, width=800, default_flow_style=False)


def slugify(text, delim=u'-'):
    if not isinstance(text, basestring):
        text = str(text)
    result = []
    for word in SLUG_REGEX.split(text.lower()):
        word = word.encode('translit/long')
        if word:
            result.append(word)
    return unicode(delim.join(result))


class DummyDict(object):

    def __getattr__(self, name):
        return ''


class JsonEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, 'timetuple'):
            return time.mktime(obj.timetuple())
        raise TypeError(repr(obj) + ' is not JSON serializable.')


def LocaleIterator(iterator, locale):
    locale = str(locale)
    for i, line in enumerate(iterator):
        if i == 0 or line.startswith(locale):
            yield line


def get_rows_from_csv(pod, path, locale=SENTINEL):
    fp = pod.open_file(path)
    if locale is not SENTINEL:
        fp = LocaleIterator(fp, locale=locale)
    rows = []
    for row in csv_lib.DictReader(fp):
        data = {}
        for header, cell in row.iteritems():
            if cell is None:
                cell = ''
            data[header] = cell.decode('utf-8')
        rows.append(data)
    return rows


def import_string(import_name, paths):
    """Imports & returns an object using dot notation, e.g. 'A.B.C'"""
    # ASSUMPTION: import_name refers to a value in a module (i.e. must have at
    # least 2 parts)
    if '.' not in import_name:
        raise ImportError
    part1, part2 = import_name.split('.', 1)
    if '.' in part2:
        f, part1_path, desc = imp.find_module(part1, paths)
        return import_string(part2, [part1_path])
    else:
        module = imp.load_module(part1, *imp.find_module(part1, paths))
        return getattr(module, part2)


class ProgressBarThread(threading.Thread):

    def __init__(self, bar, enabled, *args, **kwargs):
        self.bar = bar
        self.enabled = enabled
        super(ProgressBarThread, self).__init__(*args, **kwargs)

    def run(self):
        super(ProgressBarThread, self).run()
        if self.enabled:
            self.bar.update(self.bar.currval + 1)


def clean_html(content, convert_to_markdown=False):
    soup = bs4.BeautifulSoup(content, 'html.parser')
    _process_google_hrefs(soup)
    _process_google_comments(soup)
    # Support HTML fragments without body tags.
    content = unicode(soup.body or soup)
    if convert_to_markdown:
        h2t = html2text.HTML2Text()
        content = h2t.handle(content).strip()
    return content.encode('utf-8')


def _process_google_hrefs(soup):
    for tag in soup.find_all('a'):
        if tag.attrs.get('href'):
            tag['href'] = _clean_google_href(tag['href'])


def _process_google_comments(soup):
    for el in soup.find_all('a'):
        id_attribute = el.get('id')
        if id_attribute and id_attribute.startswith(('cmnt', 'ftnt')):
            footer_parent = el.find_parent('div')
            if footer_parent:
                footer_parent.decompose()
            sup_parent = el.find_parent('sup')
            if sup_parent:
                sup_parent.decompose()


def _clean_google_href(href):
    regex = ('^'
             + re.escape('https://www.google.com/url')
             + '(\?|.*\&)q=([^\&]*)')
    match = re.match(regex, href)
    if match:
        encoded_url = match.group(2)
        return urllib.unquote(encoded_url)
    return href


def format_existing_data(old_data, new_data, preserve=None, key_to_update=None):
    if old_data:
        if preserve == 'builtins':
            for key in old_data.keys():
                if not key.startswith('$'):
                    del old_data[key]
        if key_to_update:
            old_data[key_to_update] = new_data
        else:
            old_data.update(new_data)
        return old_data
    return new_data
