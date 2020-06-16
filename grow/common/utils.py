"""Common grow utility functions."""

import csv as csv_lib
import codecs
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
from urllib import parse as url_parse
from collections import OrderedDict
import yaml
import bs4
import git
import html2text
import translitcodec  # pylint: disable=unused-import
from grow.common import structures
from grow.common import untag
from grow.common import yaml_utils
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
DRAFT_KEY = '$draft'
SLUG_REGEX = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},\.;]+')
SLUG_SUBSTITUTE = ((':{}', ':'),)


class Error(Exception):
    """Base error class."""

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class UnavailableError(Error):
    """Raised when a feature is not available."""
    pass


class DraftStringError(Error):
    """Raised when a draft string is used yet not allowed."""
    pass


def get_grow_dir():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_git_repo(root):
    try:
        return git.Repo(root)
    except git.InvalidGitRepositoryError:
        logging.info('WARNING: No Git repository found in {}'.format(root))


def interactive_confirm(message, default=False, input_func=None):
    if input_func is None:
        input_func = lambda m: input(m).lower()

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
    try:
        return FORMATTER.vformat(base_string, args, safe_kwargs)
    except TypeError as e:
        return FORMATTER.vformat(str(base_string), args, safe_kwargs)


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
        key = (args, frozenset(list(kwargs.items())))
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
    return list(zip(l[::2], l[1::2]))


def make_base_yaml_loader(pod, locale=None, untag_params=None,
                          tracking_func=None):
    """Make a base yaml loader that does not touch collections or docs."""
    if not tracking_func:
        tracking_func = lambda *args, **kwargs: None

    # A default set of params for nested yaml parsing.
    if not untag_params and pod:
        untag_params = {
            'env': untag.UntagParamRegex(pod.env.name),
        }

    class BaseYamlLoader(yaml_Loader):

        @staticmethod
        def loader_locale():
            return locale

        @staticmethod
        def pod_path():
            return None

        @staticmethod
        def deep_reference(data, reference):
            data = structures.DeepReferenceDict(data)
            try:
                return data[reference]
            except KeyError:
                return None

        @staticmethod
        def read_csv(pod_path, locale):
            """Reads a csv file using a cache."""
            file_cache = pod.podcache.file_cache
            contents = file_cache.get(pod_path, locale=locale)
            if contents is None:
                contents = pod.read_csv(pod_path, locale=locale)
                contents = untag.Untag.untag(
                    contents, locale_identifier=locale, params=untag_params)
                file_cache.add(pod_path, contents, locale=locale)
            return contents

        @staticmethod
        def read_file(pod_path):
            """Reads a file using a cache."""
            file_cache = pod.podcache.file_cache
            contents = file_cache.get(pod_path)
            if contents is None:
                contents = pod.read_file(pod_path)
                file_cache.add(pod_path, contents)
            return contents

        @staticmethod
        def read_json(pod_path, locale):
            """Reads a json file using a cache."""
            file_cache = pod.podcache.file_cache
            contents = file_cache.get(pod_path, locale=locale)
            if contents is None:
                contents = pod.read_json(pod_path)
                contents = untag.Untag.untag(
                    contents, locale_identifier=locale, params=untag_params)
                file_cache.add(pod_path, contents, locale=locale)
            return contents

        @classmethod
        def read_string(cls, path):
            if '.' not in path:
                return None
            main, reference = path.split('.', 1)
            path = '/content/strings/{}.yaml'.format(main)
            tracking_func(path)
            if reference:
                data = structures.DeepReferenceDict(
                    cls.read_yaml(path, locale=cls.loader_locale()))
                try:
                    allow_draft = pod.podspec.fields.get('strings', {}).get('allow_draft')
                    if allow_draft is False and data.get(DRAFT_KEY):
                        raise DraftStringError('Encountered string in draft -> {}?{}'.format(path, reference))
                    value = data[reference]
                    if value is None:
                        if cls.pod_path():
                            pod.logger.warning(
                                'Missing {}.{} in {}'.format(
                                    main, reference, cls.pod_path()))
                        else:
                            pod.logger.warning(
                                'Missing {}.{}'.format(main, reference))
                    return value
                except KeyError:
                    return None
            return None

        @classmethod
        def read_yaml(cls, pod_path, locale):
            """Reads a yaml file using a cache."""
            file_cache = pod.podcache.file_cache
            contents = file_cache.get(pod_path, locale=locale)
            if contents is None:
                # Cannot use the file cache to store the raw data with the
                # `yaml.load` since constructors in the yaml loading are already
                # completed with the provided locale so untagged data is lost
                # and cannot be stored as raw data.
                contents = yaml.load(pod.read_file(pod_path), Loader=cls) or {}
                contents = untag.Untag.untag(
                    contents, locale_identifier=locale, params=untag_params)
                file_cache.add(pod_path, contents, locale=locale)
            return contents

        def _construct_func(self, node, func):
            if isinstance(node, yaml.SequenceNode):
                items = []
                for i, each in enumerate(node.value):
                    items.append(func(node.value[i].value))
                return items
            return func(node.value)

        def _track_dep_func(self, func):
            """Wrap a function with a call to the tracking function."""
            def _func(path, *args, **kwargs):
                tracking_func(path)
                return func(path, *args, **kwargs)
            return _func

        def construct_csv(self, node):
            def func(path):
                if '?' in path:
                    path, reference = path.split('?')
                    tracking_func(path)
                    return self.deep_reference(
                        self.read_csv(path, locale=self.loader_locale()), reference)
                tracking_func(path)
                return self.read_csv(path, locale=self.loader_locale())
            return self._construct_func(node, func)

        def construct_file(self, node):
            return self._construct_func(
                node, self._track_dep_func(self.read_file))

        def construct_gettext(self, node):
            return self._construct_func(node, gettext.gettext)

        def construct_json(self, node):
            def func(path):
                if '?' in path:
                    path, reference = path.split('?')
                    tracking_func(path)
                    return self.deep_reference(
                        self.read_json(path, locale=self.loader_locale()), reference)
                tracking_func(path)
                return self.read_json(path, locale=self.loader_locale())
            return self._construct_func(node, func)

        def construct_string(self, node):
            return self._construct_func(node, self.read_string)

        def construct_yaml(self, node):
            def func(path):
                if '?' in path:
                    path, reference = path.split('?')
                    tracking_func(path)
                    data = structures.DeepReferenceDict(
                        self.read_yaml(path, locale=self.loader_locale()))
                    try:
                        return data[reference]
                    except KeyError:
                        return None
                tracking_func(path)
                return self.read_yaml(path, locale=self.loader_locale())
            return self._construct_func(node, func)

    BaseYamlLoader.add_constructor('!_', BaseYamlLoader.construct_gettext)
    BaseYamlLoader.add_constructor('!g.csv', BaseYamlLoader.construct_csv)
    BaseYamlLoader.add_constructor('!g.file', BaseYamlLoader.construct_file)
    BaseYamlLoader.add_constructor('!g.json', BaseYamlLoader.construct_json)
    BaseYamlLoader.add_constructor('!g.string', BaseYamlLoader.construct_string)
    BaseYamlLoader.add_constructor('!g.yaml', BaseYamlLoader.construct_yaml)

    return BaseYamlLoader


def make_yaml_loader(pod, doc=None, locale=None, untag_params=None):
    # A default set of params for nested yaml parsing.
    if not untag_params and pod:
        untag_params = {
            'env': untag.UntagParamRegex(pod.env.name),
        }

    # Tracing function for dependency graph.
    tracking_func = lambda *args, **kwargs: None
    if pod and doc:
        # Add the path to the dependency graph in case it has no external refs.
        pod.podcache.dependency_graph.add(doc.pod_path, doc.pod_path)
        def _track_dep(path):
            pod.podcache.dependency_graph.add(doc.pod_path, path)
        tracking_func = _track_dep

    base_loader = make_base_yaml_loader(
        pod, locale=locale, untag_params=untag_params,
        tracking_func=tracking_func)

    class YamlLoader(base_loader):

        @staticmethod
        def loader_locale():
            return str(doc.locale_safe) if doc else locale

        @staticmethod
        def pod_path():
            if doc:
                return doc.pod_path
            return None

        def construct_doc(self, node):
            def func(path):
                constructed_doc = pod.get_doc(path, locale=self.loader_locale())
                if not constructed_doc.exists:
                    raise errors.DocumentDoesNotExistError(
                        'Referenced document does not exist: {}'.format(path))
                tracking_func(constructed_doc.pod_path)
                return constructed_doc
            return self._construct_func(node, func)

        def construct_static(self, node):
            def func(path):
                tracking_func(path)
                return pod.get_static(path, locale=self.loader_locale())
            return self._construct_func(node, func)

        def construct_url(self, node):
            def func(path):
                tracking_func(path)
                return pod.get_url(path, locale=self.loader_locale())
            return self._construct_func(node, func)

    YamlLoader.add_constructor('!g.doc', YamlLoader.construct_doc)
    YamlLoader.add_constructor('!g.static', YamlLoader.construct_static)
    YamlLoader.add_constructor('!g.url', YamlLoader.construct_url)

    return YamlLoader


def load_yaml(*args, **kwargs):
    pod = kwargs.pop('pod', None)
    doc = kwargs.pop('doc', None)
    untag_params = kwargs.pop('untag_params', None)
    simple_loader = kwargs.pop('simple_loader', False)
    default_locale = None
    if doc:
        default_locale = doc._locale_kwarg or doc.collection.default_locale
    locale = kwargs.pop('locale', default_locale)
    if simple_loader:
        # Simple loader does not reference collections or documents.
        loader = make_base_yaml_loader(
            pod, locale=locale, untag_params=untag_params)
    else:
        loader = make_yaml_loader(
            pod, doc=doc, locale=locale, untag_params=untag_params)
    contents = yaml.load(*args, Loader=loader, **kwargs) or {}
    if not untag_params:
        return contents
    return untag.Untag.untag(
        contents, locale_identifier=locale, params=untag_params)


def load_plain_yaml(content, pod=None, locale=None):
    return yaml.load(content, Loader=yaml_utils.PlainTextYamlLoader)


def parse_yaml(content, pod=None, locale=None, untag_params=None,
               simple_loader=False):
    return load_yaml(
        content, pod=pod, locale=locale, untag_params=untag_params,
        simple_loader=simple_loader)


def dump_yaml(obj):
    """Dumps yaml using the the safe dump."""
    return yaml.safe_dump(
        obj, allow_unicode=True, width=800, default_flow_style=False)


def dump_plain_yaml(obj):
    """Dumps yaml using the plain text dumper to retain constructors."""
    return yaml.dump(
        obj, Dumper=yaml_utils.PlainTextYamlDumper,
        default_flow_style=False, allow_unicode=True, width=800)


def ordered_dict_representer(dumper, data):
    return dumper.represent_mapping('tag:yaml.org,2002:map', list(data.items()))


yaml.SafeDumper.add_representer(OrderedDict, ordered_dict_representer)


def slugify(text, delim='-'):
    if not isinstance(text, str):
        text = str(text)
    result = []
    for word in SLUG_REGEX.split(text.lower()):
        if not isinstance(word, str):
            word = word
        word = codecs.encode(word, 'translit/long')
        if word:
            result.append(word)
    slug = str(delim.join(result))
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
        for header, cell in row.items():
            if cell is None:
                cell = ''
            data[header] = cell
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
    content = str(soup.body or soup)
    if convert_to_markdown:
        h2t = html2text.HTML2Text()
        h2t.body_width = 0  # https://github.com/grow/grow/issues/887
        # Fixes a bug with malformed tables from Google Doc integration.
        # Preserves tables as <table> tags.
        h2t.bypass_tables = True
        h2t.single_line_break = False
        content = h2t.handle(content).strip()
    return content


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
        return url_parse.unquote(encoded_url)
    return href


def format_existing_data(old_data, new_data, preserve=None, key_to_update=None):
    if old_data:
        if preserve == 'builtins':
            for key in list(old_data.keys()):
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
