from datetime import datetime
from grow.common import utils
from grow.pods import locales as locales_lib
from grow.pods.collectionz import collectionz
import collections
import csv as csv_lib
import itertools
import jinja2
import json
import markdown
import re



def categories(collection=None, collections=None, reverse=None, order_by=None, _pod=None):
  if isinstance(collection, collectionz.Collection):
    collection = collection
  elif isinstance(collection, basestring):
    collection = _pod.get_collection(collection)
  else:
    text = '{} must be a Collection instance or a collection path, found: {}.'
    raise ValueError(text.format(collection, type(collection)))

  category_list = collection.list_categories()
  def order_func(doc):
    return category_list.index(doc.category)

  docs = [doc for doc in collection.list_documents(reverse=reverse, order_by='order')]
  docs = sorted(docs, key=order_func)
  items = itertools.groupby(docs, key=order_func)
  return ((category_list[index], pages) for index, pages in items)


def LocaleIterator(iterator, locale):
  locale = str(locale)
  for i, line in enumerate(iterator):
    if i == 0 or line.startswith(locale):
      yield line

_no_locale = '__no_locale'

def csv(path, locale=_no_locale, _pod=None):
  fp = _pod.open_file(path)
  if locale is not _no_locale:
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


def docs(collection, locale=None, order_by=None, _pod=None):
  collection = _pod.get_collection(collection)
  return collection.search_docs(locale=locale, order_by=order_by)


def markdown_filter(value):
  try:
    if isinstance(value, unicode):
      value = value.decode('utf-8')
    return markdown.markdown(value)
  except UnicodeEncodeError:
    return markdown.markdown(value)


_slug_regex = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')
def slug_filter(value):
  result = []
  for word in _slug_regex.split(value.lower()):
    if word:
      result.append(word)
  return unicode(u'-'.join(result))


def static(path, _pod=None):
  # TODO(jeremydw): Implement this.
  return path


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


def nav(collection=None, locale=None, _pod=None):
  collection_obj = _pod.get_collection('/content/' + collection)
  results = collection_obj.search_docs(order_by='order', locale=locale)
  menu = Menu()
  menu.build(results)
  return menu


def breadcrumb(doc, _pod=None):
  pass


def url(pod_path, locale=None, _pod=None):
  doc = _pod.get_doc(pod_path, locale=locale)
  return doc.url


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
  return json.dumps(obj, *args, **kwargs)


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


def yaml(path, _doc, _pod):
  catalog = _pod.catalogs.get(_doc.locale) if _doc else None
  fields = utils.parse_yaml(_pod.read_file(path))
  return utils.untag_fields(fields, catalog=catalog)


def date(datetime_obj=None, _pod=None, **kwargs):
  _from = kwargs.get('from', None)
  if datetime_obj is None:
    datetime_obj = datetime.now()
  elif isinstance(datetime_obj, basestring) and _from is not None:
    datetime_obj = datetime.strptime(datetime_obj, _from)
  return datetime_obj


def locales(codes, _pod=None):
  return locales_lib.Locale.parse_codes(codes)
