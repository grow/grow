from grow.pods import errors
try:
    import cStringIO as StringIO
except ImportError:
    try:
        import StringIO
    except ImportError:
        from io import StringIO
import csv as csv_lib
import functools
import gettext
import imp
import json
import logging
import os
import re
import sys
import threading
import time
import translitcodec
import yaml

# The CLoader implementation of the PyYaml loader is orders of magnitutde
# faster than the default pure Python loader. CLoader is available when
# libyaml is installed on the system.
try:
    from yaml import CLoader as yaml_Loader
except ImportError:
    logging.warning('Warning: libyaml missing, using slower yaml parser.')
    from yaml import Loader as yaml_Loader


SENTINEL = object()


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


def interactive_confirm(message, default=False):
    message = '{} [y/N]: '.format(message)
    choice = raw_input(message).lower()
    if choice == 'y':
        return True
    return False


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
            locale = doc.locale if doc else None
            func = lambda path: pod.get_doc(path, locale=locale)
            return self._construct_func(node, func)

        def construct_gettext(self, node):
            return self._construct_func(node, gettext.gettext)

        def construct_json(self, node):
            return self._construct_func(node, pod.read_json)

        def construct_static(self, node):
            locale = doc.locale if doc else None
            func = lambda path: pod.get_static(path, locale=locale)
            return self._construct_func(node, func)

        def construct_url(self, node):
            locale = doc.locale if doc else None
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


_slug_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim=u'-'):
    if not isinstance(text, basestring):
        text = str(text)
    result = []
    for word in _slug_re.split(text.lower()):
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


@memoize
def untag_fields(fields):
    """Untags fields, handling translation priority."""
    untagged_keys_to_add = {}
    nodes_and_keys_to_add = []
    nodes_and_keys_to_remove = []
    def callback(item, key, node):
        if not isinstance(key, basestring):
            return
        if key.endswith('@#'):
            nodes_and_keys_to_remove.append((node, key))
        if key.endswith('@'):
            untagged_key = key.rstrip('@')
            content = item
            nodes_and_keys_to_remove.append((node, key))
            untagged_keys_to_add[untagged_key] = True
            nodes_and_keys_to_add.append((node, untagged_key, content))
    walk(fields, callback)
    for node, key in nodes_and_keys_to_remove:
        if isinstance(node, dict):
            del node[key]
    for node, untagged_key, content in nodes_and_keys_to_add:
        if isinstance(node, dict):
            node[untagged_key] = content
    return fields


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
