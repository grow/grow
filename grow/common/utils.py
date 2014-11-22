from grow.pods import errors
import functools
import git
import json
import logging
import mimetypes
import os
import re
import sys
import time
import translitcodec
import yaml


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


def walk(node, callback):
  if node is None:
    return
  for key in node:
    item = node[key] if isinstance(node, dict) else key
    if isinstance(item, (list, set, dict)):
      walk(item, callback)
    else:
      callback(item, key, node)


def apply_heaers(headers, path):
  mimetype = mimetypes.guess_type(path)[0]
  if mimetype:
    headers['Content-Type'] = mimetype


def validate_name(name):
  # TODO: better validation.
  if ('//' in name
      or '..' in name
      or ' ' in name):
    raise errors.BadNameError(
        'Name must be lowercase and only contain letters, numbers, '
        'backslashes, and dashes. Found: "{}"'.format(name))


class memoize(object):

  def __init__(self, func):
    self.func = func
    self.cache = {}

  def __call__(self, *args):
    try:
      return self.cache[args]
    except KeyError:
      value = self.func(*args)
      self.cache[args] = value
      return value
    except TypeError:
      return self.func(*args)

  def __repr__(self):
    return self.func.__doc__

  def __get__(self, obj, objtype):
    fn = functools.partial(self.__call__, obj)
    fn.reset = self._reset
    return fn

  def _reset(self):
    self.cache = {}


def every_two(l):
  return zip(l[::2], l[1::2])


def parse_yaml(content):
  return yaml.load(content)


def dump_yaml(obj):
  return yaml.safe_dump(obj, allow_unicode=True, width=800, default_flow_style=False)


_slug_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slugify(text, delim=u'-'):
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
