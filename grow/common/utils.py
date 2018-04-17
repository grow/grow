"""Common grow utility functions."""

import csv as csv_lib
import fnmatch
import functools
import gettext
import json
import logging
import os
import re
import string
import sys
import threading
import time
import urllib
import yaml
import bs4
import html2text
import translitcodec  # pylint: disable=unused-import
from collections import OrderedDict
from grow.common import structures
from grow.documents import document_fields
from grow.pods import errors

# The CLoader implementation of the PyYaml loader is orders of magnitutde
# faster than the default pure Python loader. CLoader is available when
# libyaml is installed on the system.
try:
    # pylint: disable=ungrouped-imports
    from yaml import CLoader as yaml_Loader
except ImportError:
    logging.warning('Warning: libyaml missing, using slower yaml parser.')
    from yaml import Loader as yaml_Loader


LOCALIZED_KEY_REGEX = re.compile('(.*)@([^@]+)$')
SENTINEL = object()
SLUG_REGEX = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
SLUG_SUBSTITUTE = ((':{}', ':'),)


class Error(Exception):
    """Base error class."""


class UnavailableError(Error):
    """Raised when a feature is not available."""


def is_packaged_app():
    """Returns whether the environment is a packaged app."""
    try:
        # pylint: disable=pointless-statement,protected-access
        sys._MEIPASS
        return True
    except AttributeError:
        return False


def is_appengine():
    """Returns whether the environment is Google App Engine."""
    if 'SERVER_SOFTWARE' in os.environ:
        # https://cloud.google.com/appengine/docs/standard/python/how-requests-are-handled
        return os.environ['SERVER_SOFTWARE'].startswith(('Development/', 'Google App Engine/'))
    return False


def get_git():
    """Returns the git module if it is available."""
    if not is_appengine():
        import git
        return git
    raise UnavailableError('Git is not available in this environment.')


def get_grow_dir():
    if is_packaged_app():
        # pylint: disable=no-member,protected-access
        return os.path.join(sys._MEIPASS)
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_cacerts_path():
    return os.path.join(get_grow_dir(), 'data', 'cacerts.txt')


def get_git_repo(root):
    git = get_git()
    try:
        return git.Repo(root)
    except git.InvalidGitRepositoryError:
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


FORMATTER = string.Formatter()
def safe_format(base_string, *args, **kwargs):
    """Safely format a string using the modern string formatting with fallback."""
    safe_kwargs = structures.SafeDict(**kwargs)
    return FORMATTER.vformat(base_string, args, safe_kwargs)


def walk(node, callback, parent_key=None, parent_node=None):
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
            walk(item, callback, parent_key=parent_key, parent_node=node)
        else:
            if isinstance(node, (list, set)):
                key = parent_key
            callback(item, key, node, parent_node=parent_node)


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


def make_yaml_loader(pod, doc=None, locale=None):
    loader_locale = locale

    class YamlLoader(yaml_Loader):

        @staticmethod
        def read_csv(pod_path):
            """Reads a csv file using a cache."""
            file_cache = pod.podcache.file_cache
            contents = file_cache.get(pod_path)
            if contents is None:
                contents = pod.read_csv(pod_path)
                file_cache.add(pod_path, contents)
            return contents

        @staticmethod
        def read_json(pod_path):
            """Reads a json file using a cache."""
            file_cache = pod.podcache.file_cache
            contents = file_cache.get(pod_path)
            if contents is None:
                contents = pod.read_json(pod_path)
                file_cache.add(pod_path, contents)
            return contents

        @staticmethod
        def read_yaml(pod_path, locale):
            """Reads a yaml file using a cache."""
            file_cache = pod.podcache.file_cache
            contents = file_cache.get(pod_path, locale=locale)
            if contents is None:
                contents = pod.read_yaml(pod_path, locale=locale)
                file_cache.add(pod_path, contents, locale=locale)
            return contents

        def _construct_func(self, node, func):
            if isinstance(node, yaml.SequenceNode):
                items = []
                for i, each in enumerate(node.value):
                    items.append(func(node.value[i].value))
                return items
            return func(node.value)

        def construct_csv(self, node):
            def func(path):
                if doc:
                    pod.podcache.dependency_graph.add(doc.pod_path, path)
                return self.read_csv(path)
            return self._construct_func(node, func)

        def construct_doc(self, node):
            locale = str(doc.locale_safe) if doc else loader_locale
            pod_path = doc.pod_path if doc else None

            def func(path):
                contructed_doc = pod.get_doc(path, locale=locale)
                pod.podcache.dependency_graph.add(
                    pod_path, contructed_doc.pod_path)
                return contructed_doc
            return self._construct_func(node, func)

        def construct_gettext(self, node):
            return self._construct_func(node, gettext.gettext)

        def construct_json(self, node):
            if doc:
                pod.podcache.dependency_graph.add(doc.pod_path, node.value)
            return self._construct_func(node, self.read_json)

        def construct_static(self, node):
            locale = str(doc.locale_safe) if doc else loader_locale

            def func(path):
                if doc:
                    pod.podcache.dependency_graph.add(doc.pod_path, path)
                return pod.get_static(path, locale=locale)
            return self._construct_func(node, func)

        def construct_string(self, node):
            def func(path):
                if '.' not in path:
                    return None
                main, reference = path.split('.', 1)
                path = '/content/strings/{}.yaml'.format(main)
                locale = str(doc.locale_safe) if doc else loader_locale
                if doc:
                    pod.podcache.dependency_graph.add(doc.pod_path, path)
                if reference:
                    data = structures.DeepReferenceDict(self.read_yaml(path, locale=locale))
                    try:
                        value = data[reference]
                        if value is None:
                            if doc:
                                pod.logger.warning(
                                    'Missing {}.{} in {}'.format(
                                        main, reference, doc.pod_path))
                            else:
                                pod.logger.warning(
                                    'Missing {}.{}'.format(main, reference))
                        return data[reference]
                    except KeyError:
                        return None
                return None
            return self._construct_func(node, func)

        def construct_url(self, node):
            locale = str(doc.locale_safe) if doc else loader_locale

            def func(path):
                if doc:
                    pod.podcache.dependency_graph.add(doc.pod_path, path)
                return pod.get_url(path, locale=locale)
            return self._construct_func(node, func)

        def construct_yaml(self, node):
            def func(path):
                locale = str(doc.locale_safe) if doc else loader_locale
                if '?' in path:
                    path, reference = path.split('?')
                    if doc:
                        pod.podcache.dependency_graph.add(doc.pod_path, path)
                    data = structures.DeepReferenceDict(self.read_yaml(path, locale=locale))
                    try:
                        return data[reference]
                    except KeyError:
                        return None
                if doc:
                    pod.podcache.dependency_graph.add(doc.pod_path, path)
                return self.read_yaml(path, locale=locale)
            return self._construct_func(node, func)

    YamlLoader.add_constructor(u'!_', YamlLoader.construct_gettext)
    YamlLoader.add_constructor(u'!g.csv', YamlLoader.construct_csv)
    YamlLoader.add_constructor(u'!g.doc', YamlLoader.construct_doc)
    YamlLoader.add_constructor(u'!g.json', YamlLoader.construct_json)
    YamlLoader.add_constructor(u'!g.static', YamlLoader.construct_static)
    YamlLoader.add_constructor(u'!g.string', YamlLoader.construct_string)
    YamlLoader.add_constructor(u'!g.url', YamlLoader.construct_url)
    YamlLoader.add_constructor(u'!g.yaml', YamlLoader.construct_yaml)
    return YamlLoader


def load_yaml(*args, **kwargs):
    pod = kwargs.pop('pod', None)
    doc = kwargs.pop('doc', None)
    locale = kwargs.pop('locale', None)
    loader = make_yaml_loader(pod, doc=doc, locale=locale)
    return yaml.load(*args, Loader=loader, **kwargs) or {}


@memoize
def parse_yaml(content, pod=None, locale=None):
    return load_yaml(content, pod=pod, locale=locale)


def dump_yaml(obj):
    return yaml.safe_dump(
        obj, allow_unicode=True, width=800, default_flow_style=False)


def ordered_dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', data.items())


yaml.SafeDumper.add_representer(OrderedDict, ordered_dict_representer)


def slugify(text, delim=u'-'):
    if not isinstance(text, basestring):
        text = str(text)
    result = []
    for word in SLUG_REGEX.split(text.lower()):
        word = word.encode('translit/long')
        if word:
            result.append(word)
    slug = unicode(delim.join(result))
    for seq, sub in SLUG_SUBSTITUTE:
        slug = slug.replace(seq.format(delim), sub.format(delim))
    return slug


class DummyDict(object):

    def __getattr__(self, name):
        return ''


class JsonEncoder(json.JSONEncoder):

    # pylint: disable=method-hidden
    def default(self, o):
        if hasattr(o, 'timetuple'):
            return time.mktime(o.timetuple())
        raise TypeError(repr(o) + ' is not JSON serializable.')


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


class ProgressBarThread(threading.Thread):

    def __init__(self, bar, enabled, *args, **kwargs):
        self.bar = bar
        self.enabled = enabled
        super(ProgressBarThread, self).__init__(*args, **kwargs)

    def run(self):
        super(ProgressBarThread, self).run()
        if self.enabled:
            self.bar.update(self.bar.value + 1)


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
    if key_to_update:
        return {key_to_update: new_data}
    return new_data


def fnmatches_paths(path_to_extract, paths):
    # Special case: user doesn't want to check against any paths.
    if not paths:
        return True
    for path in paths:
        # Support pod paths and filesystem paths for tab completion.
        path_to_extract = path_to_extract.lstrip('/')
        path = path.lstrip('/')
        matched = fnmatch.fnmatch(path_to_extract, path)
        if matched:
            return True
    return False
