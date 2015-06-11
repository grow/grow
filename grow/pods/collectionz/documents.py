from . import formats
from . import messages
from grow.common import utils
from grow.pods import locales
from grow.pods import urls
import copy
import json
import logging
import os
import re
import webapp2


class Error(Exception):
  pass


class DocumentDoesNotExistError(Error, ValueError):
  pass


class DocumentExistsError(Error, ValueError):
  pass


class DummyDict(object):

  def __getattr__(self, name):
    return ''


class Document(object):

  def __init__(self, pod_path, _pod, locale=None, _collection=None, body_format=None):
    utils.validate_name(pod_path)
    self.default_locale = _pod.podspec.default_locale
    self.locale = locale or _pod.podspec.default_locale
    if isinstance(self.locale, basestring):
      self.locale = locales.Locale(self.locale)
    if self.locale is not None:
      self.locale.set_alias(_pod)
    self.pod_path = pod_path
    self.basename = os.path.basename(pod_path)
    self.base, self.ext = os.path.splitext(self.basename)
    self.pod = _pod
    self.collection = _collection

  def __repr__(self):
    if self.locale:
      return "<Document({}, locale='{}')>".format(self.pod_path, self.locale)
    return "<Document({})>".format(self.pod_path)

  def __cmp__(self, other):
    return self.pod_path == other.pod_path and self.pod == other.pod

  def __ne__(self, other):
    return self.pod_path != other.pod_path or self.pod != other.pod

  def __getattr__(self, name):
    if name in self.fields:
      return self.fields[name]
    return object.__getattribute__(self, name)

  @webapp2.cached_property
  def fields(self):
    catalog = self.pod.catalogs.get(self.locale)
    fields = utils.untag_fields(copy.deepcopy(self.tagged_fields),
                                catalog=catalog)
    if fields is None:
      return {}
    return fields

  @webapp2.cached_property
  def format(self):
    return formats.Format.get(self)

  @webapp2.cached_property
  def tagged_fields(self):
    return self.format.fields

  @property
  def url(self):
    path = self.get_serving_path()
    return urls.Url(path=path) if path else None

  @property
  def slug(self):
    if '$slug' in self.fields:
      return self.fields['$slug']
    return utils.slugify(self.title) if self.title is not None else None

  @property
  def order(self):
    return self.fields.get('$order')

  @property
  def title(self):
    return self.fields.get('$title')

  def titles(self, title_name=None):
    if title_name is None:
      return self.title
    titles = self.fields.get('$titles', {})
    return titles.get(title_name, self.title)

  @property
  def category(self):
    return self.fields.get('$category')

  @property
  def date(self):
    return self.fields.get('$date')

  def dates(self, date_name=None):
    if date_name is None:
      return self.date
    dates = self.fields.get('$dates', {})
    return dates.get(date_name, self.date)

  def delete(self):
    self.pod.delete_file(self.pod_path)

  def exists(self):
    return self.pod.file_exists(self.pod_path)

  def has_collection(self):
    return self.collection.exists()

  def has_url(self):
    return True

  def get_view(self):
    view_format = self.fields.get('$view', self.collection.get_view())
    return self._format_path(view_format) if view_format is not None else None

  def get_path_format(self):
    val = None
    if (self.locale
        and self.default_locale
        and self.locale != self.default_locale):
      if ('$localization' in self.fields
          and 'path' in self.fields['$localization']):
        val = self.fields['$localization']['path']
      elif self.collection.localization:
        val = self.collection.localization['path']
    if val is None:
      return self.fields.get('$path', self.collection.get_path_format())
    return val

  def validate_route_params(self, route_params):
    pass

  @property
  @utils.memoize
  def parent(self):
    if '$parent' not in self.fields:
      return None
    parent_pod_path = self.fields['$parent']
    return self.collection.get_doc(parent_pod_path, locale=self.locale)

  def get_serving_path(self):
    # Get root path.
    locale = str(self.locale)
    config = self.pod.get_podspec().get_config()
    root_path = config.get('flags', {}).get('root_path', '')
    if locale == self.default_locale:
      root_path = config.get('localization', {}).get('root_path', root_path)
    path_format = (self.get_path_format()
        .replace('<grow:locale>', '{locale}')
        .replace('<grow:slug>', '{slug}')
        .replace('<grow:published_year>', '{published_year}'))

    # Prevent double slashes when combining root path and path format.
    if path_format.startswith('/') and root_path.endswith('/'):
      root_path = root_path[0:len(root_path)-1]
    path_format = root_path + path_format

    # Handle default date formatting in the url.
    while '{date|' in path_format:
      re_date = r'({date\|(?P<date_format>[a-zA-Z0-9_%-]+)})'
      match = re.search(re_date, path_format)
      if match:
        formatted_date = self.date
        formatted_date = formatted_date.strftime(match.group('date_format'))
        path_format = path_format[:match.start()] + formatted_date + path_format[match.end():]
      else:
        # Does not match expected format, let the normal format attempt it.
        break;

    # Handle the special formatting of dates in the url.
    while '{dates.' in path_format:
      re_dates = r'({dates\.(?P<date_name>\w+)(\|(?P<date_format>[a-zA-Z0-9_%-]+))?})'
      match = re.search(re_dates, path_format)
      if match:
        formatted_date = self.dates(match.group('date_name'))
        formatted_date = formatted_date.strftime(match.group('date_format') or '%Y-%m-%d')
        path_format = path_format[:match.start()] + formatted_date + path_format[match.end():]
      else:
        # Does not match expected format, let the normal format attempt it.
        break;

    try:
      return self._format_path(path_format)
    except KeyError:
      logging.error('Error with path format: {}'.format(path_format))
      raise

  def _format_path(self, path_format):
    podspec = self.pod.get_podspec()
    return path_format.format(**{
        'base': os.path.splitext(os.path.basename(self.pod_path))[0],
        'date': self.date,
        'locale': self.locale.alias if self.locale is not None else self.locale,
        'parent': self.parent if self.parent else DummyDict(),
        'podspec': podspec,
        'slug': self.slug,
    }).replace('//', '/')

  @property
  def locales(self):
    return self.list_locales()

  def list_locales(self):
    if ('$localization' in self.fields
        and 'locales' in self.fields['$localization']):
      codes = self.fields['$localization']['locales']
      return locales.Locale.parse_codes(codes)
    return self.collection.list_locales()

  @property
  @utils.memoize
  def body(self):
    body = self.format.body
    if body is None:
      return body
    return body.decode('utf-8')

  @property
  def content(self):
    content = self.format.content
    return content.decode('utf-8')

  @property
  def html(self):
    return self.format.html

  @property
  def hidden(self):
    return self.fields.get('$hidden', False)

  def __eq__(self, other):
    return (isinstance(self, Document)
            and isinstance(other, Document)
            and self.pod_path == other.pod_path)

  def next(self, docs=None):
    # TODO(jeremydw): Verify items is a list of docs.
    if docs is None:
      docs = self.collection.search_docs()
    for i, doc in enumerate(docs):
      if doc == self:
        n = i + 1
        if n == len(docs):
          return None
        return docs[i + 1]

  def prev(self, docs=None):
    # TODO(jeremydw): Verify items is a list of docs.
    if docs is None:
      docs = self.collection.search_docs()
    for i, doc in enumerate(docs):
      if doc == self:
        n = i - 1
        if n < 0:
          return None
        return docs[i - 1]

  def create_from_message(self, message):
    if self.exists():
      raise DocumentExistsError('{} already exists.'.format(self))
    self.update_from_message(message)

  def update_from_message(self, message):
    if message.content is not None:
      if isinstance(message.content, unicode):
        content = message.content.encode('utf-8')
      else:
        content = message.content
      self.format.write(content)
    elif message.fields is not None:
      content = '---\n{}\n---\n{}\n'.format(message.fields, message.body or '')
      self.format.write(content)
      self.fields = self.format.fields
    else:
      raise NotImplementedError()

  def to_message(self):
    message = messages.DocumentMessage()
    message.basename = self.basename
    message.pod_path = self.pod_path
    message.collection_path = self.collection.collection_path
    message.body = self.body
    message.content = self.content
    message.fields = json.dumps(self.fields, cls=utils.JsonEncoder)
    message.serving_path = self.get_serving_path()
    return message
