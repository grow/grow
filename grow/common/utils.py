from grow.pods import errors
import functools
import gettext
import git
import json
import logging
import os
import re
import sys
import cStringIO
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


def is_packaged_app():
  try:
    sys._MEIPASS
    return True
  except AttributeError:
    return False


def get_grow_dir():
  if is_packaged_app():
    return os.path.join(sys._MEIPASS)
  return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


def get_cacerts_path():
  return os.path.join(get_grow_dir(), 'data', 'cacerts.txt')


def get_git_repo(root):
  try:
    return git.Repo(root)
  except git.exc.InvalidGitRepositoryError:
    logging.info('Warning: {} is not a Git repository.'.format(root))


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


def make_yaml_loader(pod):
  class YamlLoader(yaml_Loader):

    def construct_gettext(self, node):
      if isinstance(node, yaml.SequenceNode):
        items = []
        for i, each in enumerate(node.value):
          items.append(gettext.gettext(node.value[i].value))
        return items
      return gettext.gettext(node.value)

    def construct_doc(self, node):
      if isinstance(node, yaml.SequenceNode):
        items = []
        for i, each in enumerate(node.value):
          items.append(pod.get_doc(node.value[i].value))
        return items
      return pod.get_doc(node.value)

  YamlLoader.add_constructor(u'!_', YamlLoader.construct_gettext)
  YamlLoader.add_constructor(u'!g.doc', YamlLoader.construct_doc)
  return YamlLoader


def load_yaml(*args, **kwargs):
  pod = kwargs.pop('pod', None)
  loader = make_yaml_loader(pod)
  return yaml.load(*args, Loader=loader, **kwargs)


def load_yaml_all(*args, **kwargs):
  pod = kwargs.pop('pod', None)
  fp = cStringIO.StringIO()
  fp.write(args[0])
  fp.seek(0)
  loader = make_yaml_loader(pod)
  return yaml.load_all(*args, Loader=loader, **kwargs)


@memoize
def parse_yaml(content, pod=None):
  return load_yaml(content, pod=pod)


def dump_yaml(obj):
  return yaml.safe_dump(obj, allow_unicode=True, width=800, default_flow_style=False)


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
