from bisect import bisect_left, bisect_right
from grow.pods import errors
import json
import logging
import mimetypes
import os
import re
import sys
import time
import yaml


def get_grow_dir():
  try:
    return os.path.join(sys._MEIPASS)
  except AttributeError:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))


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


def colorize(text):
  return text.format(**{
    'blue': '\033[0;34m',
    '/blue': '\033[0;m',
    'red': '\033[0;31m',
    '/red': '\033[0;m',
    'green': '\033[0;32m',
    '/green': '\033[0;m',
    'yellow': '\033[0;33m',
    '/yellow': '\033[0;m',
    'white': '\033[0;37m',
    '/white': '\033[0;m',
  })


def apply_heaers(headers, path):
  mimetype = mimetypes.guess_type(path)[0]
  if mimetype:
    headers['Content-Type'] = mimetype


def validate_name(name):
  # TODO: better validation.
  if ('//' in name
      or '..' in name
      or ' ' in name):
    raise errors.BadNameError('Name must be lowercase and only contain letters, numbers, backslashes, and dashes. Found: "{}"'.format(name))


def memoize(f):
  class memodict(dict):
    def __init__(self, f):
      self.f = f
    def __call__(self, *args):
      return self[args]
    def __missing__(self, key):
      ret = self[key] = self.f(*key)
      return ret
  return memodict(f)


def every_two(l):
  return zip(l[::2], l[1::2])


def parse_markdown(content, path=None, locale=None, default_locale=None):
  # TODO: better parsing + only accept Locale objects.
  locale = str(locale) if locale is not None else locale
  default_locale = str(default_locale) if default_locale is not None else default_locale
  locales_to_contents = {}

  parts = re.split('(?:^|[\n])---', content, re.DOTALL)
  if len(parts) <= 1:
    return None, content

  parts = parts[1:]   # Strip off empty group.
  for fields, content in every_two(parts):
    fields = yaml.load(fields)
    doc_locale = fields.get('$locale', default_locale)
    locales_to_contents[doc_locale] = (fields, content)

  # TODO(jeremydw): Allow user to control cascading behavior, but for now,
  # combine all fields between localized document and default document. The
  # localized fields take precedence.
  if default_locale in locales_to_contents:
    fields, content = locales_to_contents[default_locale]
  else:
    fields, content = (None, None)
  if locale in locales_to_contents:
    localized_fields, localized_content = locales_to_contents[locale]
    if not fields:
      fields = {}
    fields.update(localized_fields)
    content = localized_content
  return fields, (content.strip() if content else None)


def parse_yaml(content, path=None):
  try:
    content = content.strip()
    parts = re.split('---\n', content)
    if len(parts) == 1:
      return yaml.load(content), None
    parts.pop(0)
    front_matter, body = parts
    parsed_yaml = yaml.load(front_matter)
    body = str(body)
    return parsed_yaml, body
  except Exception as e:
    if path:
      text = 'Problem parsing YAML file "{}": {}'.format(path, str(e))
    else:
      text = 'Problem parsing YAML file: {}'.format(str(e))
    logging.exception(e)
    raise errors.BadYamlError(text)


def dump_yaml(obj):
  return yaml.safe_dump(obj, allow_unicode=True, width=800, default_flow_style=False)


_slug_re = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
import translitcodec


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


class SortedCollection(object):
    '''Sequence sorted by a key function.

    SortedCollection() is much easier to work with than using bisect() directly.
    It supports key functions like those use in sorted(), min(), and max().
    The result of the key function call is saved so that keys can be searched
    efficiently.

    Instead of returning an insertion-point which can be hard to interpret, the
    five find-methods return a specific item in the sequence. They can scan for
    exact matches, the last item less-than-or-equal to a key, or the first item
    greater-than-or-equal to a key.

    Once found, an item's ordinal position can be located with the index() method.
    New items can be added with the insert() and insert_right() methods.
    Old items can be deleted with the remove() method.

    The usual sequence methods are provided to support indexing, slicing,
    length lookup, clearing, copying, forward and reverse iteration, contains
    checking, item counts, item removal, and a nice looking repr.

    Finding and indexing are O(log n) operations while iteration and insertion
    are O(n).  The initial sort is O(n log n).

    The key function is stored in the 'key' attibute for easy introspection or
    so that you can assign a new key function (triggering an automatic re-sort).

    In short, the class was designed to handle all of the common use cases for
    bisect but with a simpler API and support for key functions.

    >>> from pprint import pprint
    >>> from operator import itemgetter

    >>> s = SortedCollection(key=itemgetter(2))
    >>> for record in [
    ...         ('roger', 'young', 30),
    ...         ('angela', 'jones', 28),
    ...         ('bill', 'smith', 22),
    ...         ('david', 'thomas', 32)]:
    ...     s.insert(record)

    >>> pprint(list(s))         # show records sorted by age
    [('bill', 'smith', 22),
     ('angela', 'jones', 28),
     ('roger', 'young', 30),
     ('david', 'thomas', 32)]

    >>> s.find_le(29)           # find oldest person aged 29 or younger
    ('angela', 'jones', 28)
    >>> s.find_lt(28)           # find oldest person under 28
    ('bill', 'smith', 22)
    >>> s.find_gt(28)           # find youngest person over 28
    ('roger', 'young', 30)

    >>> r = s.find_ge(32)       # find youngest person aged 32 or older
    >>> s.index(r)              # get the index of their record
    3
    >>> s[3]                    # fetch the record at that index
    ('david', 'thomas', 32)

    >>> s.key = itemgetter(0)   # now sort by first name
    >>> pprint(list(s))
    [('angela', 'jones', 28),
     ('bill', 'smith', 22),
     ('david', 'thomas', 32),
     ('roger', 'young', 30)]

    '''

    def __init__(self, iterable=(), key=None):
        self._given_key = key
        key = (lambda x: x) if key is None else key
        decorated = sorted((key(item), item) for item in iterable)
        self._keys = [k for k, item in decorated]
        self._items = [item for k, item in decorated]
        self._key = key

    def _getkey(self):
        return self._key

    def _setkey(self, key):
        if key is not self._key:
            self.__init__(self._items, key=key)

    def _delkey(self):
        self._setkey(None)

    key = property(_getkey, _setkey, _delkey, 'key function')

    def clear(self):
        self.__init__([], self._key)

    def copy(self):
        return self.__class__(self, self._key)

    def __len__(self):
        return len(self._items)

    def __getitem__(self, i):
        return self._items[i]

    def __iter__(self):
        return iter(self._items)

    def __reversed__(self):
        return reversed(self._items)

    def __repr__(self):
        return '%s(%r, key=%s)' % (
            self.__class__.__name__,
            self._items,
            getattr(self._given_key, '__name__', repr(self._given_key))
        )

    def __reduce__(self):
        return self.__class__, (self._items, self._given_key)

    def __contains__(self, item):
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return item in self._items[i:j]

    def index(self, item):
        'Find the position of an item.  Raise ValueError if not found.'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].index(item) + i

    def count(self, item):
        'Return number of occurrences of item'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        j = bisect_right(self._keys, k)
        return self._items[i:j].count(item)

    def insert(self, item):
        'Insert a new item.  If equal keys are found, add to the left'
        k = self._key(item)
        i = bisect_left(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def insert_right(self, item):
        'Insert a new item.  If equal keys are found, add to the right'
        k = self._key(item)
        i = bisect_right(self._keys, k)
        self._keys.insert(i, k)
        self._items.insert(i, item)

    def remove(self, item):
        'Remove first occurence of item.  Raise ValueError if not found'
        i = self.index(item)
        del self._keys[i]
        del self._items[i]

    def find(self, k):
        'Return first item with a key == k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i != len(self) and self._keys[i] == k:
            return self._items[i]
        raise ValueError('No item found with key equal to: %r' % (k,))

    def find_le(self, k):
        'Return last item with a key <= k.  Raise ValueError if not found.'
        i = bisect_right(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key at or below: %r' % (k,))

    def find_lt(self, k):
        'Return last item with a key < k.  Raise ValueError if not found.'
        i = bisect_left(self._keys, k)
        if i:
            return self._items[i-1]
        raise ValueError('No item found with key below: %r' % (k,))

    def find_ge(self, k):
        'Return first item with a key >= equal to k.  Raise ValueError if not found'
        i = bisect_left(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key at or above: %r' % (k,))

    def find_gt(self, k):
        'Return first item with a key > k.  Raise ValueError if not found'
        i = bisect_right(self._keys, k)
        if i != len(self):
            return self._items[i]
        raise ValueError('No item found with key above: %r' % (k,))
