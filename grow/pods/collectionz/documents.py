from grow.common import markdown_extensions
from grow.common import utils
from grow.pods import urls
from grow.pods import locales
from . import messages
import json
import logging
import markdown
import os
import copy
import re
from markdown.extensions import tables
from markdown.extensions import toc


class Error(Exception):
  pass


class BadFormatError(Error, ValueError):
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
    self._default_locale = _pod.podspec.default_locale

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

    self.format = messages.extensions_to_formats.get(self.ext)
    if self.format == messages.Format.MARKDOWN:
      self.doc_storage = MarkdownDocumentStorage(
          self.pod_path, self.pod, locale=locale, default_locale=self._default_locale)
    elif self.format == messages.Format.YAML:
      self.doc_storage = YamlDocumentStorage(
          self.pod_path, self.pod, locale=locale, default_locale=self._default_locale)
    elif self.format == messages.Format.HTML:
      self.doc_storage = HtmlDocumentStorage(
          self.pod_path, self.pod, locale=locale, default_locale=self._default_locale)
    else:
      formats = messages.extensions_to_formats.keys()
      text = 'Basename "{}" does not have a valid extension. Valid formats are: {}'
      raise BadFormatError(text.format(self.basename, ', '.join(formats)))

    self.fields = self.doc_storage.fields
    self.tagged_fields = self.doc_storage.tagged_fields

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
  def is_hidden(self):
    return bool(self.fields.get('$hidden'))

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
        and self._default_locale
        and self.locale != self._default_locale):
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
    if locale == self._default_locale:
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
    body = self.doc_storage.body
    if body is None:
      return body
    return body.decode('utf-8')

  @property
  def content(self):
    content = self.doc_storage.content
    return content.decode('utf-8')

  @property
  def html(self):
    # TODO(jeremydw): Add ability to render HTML.
    return self.doc_storage.html(self)

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
      self.doc_storage.write(content)
    elif message.fields is not None:
      content = '---\n{}\n---\n{}\n'.format(message.fields, message.body or '')
      self.doc_storage.write(content)
      self.doc_storage.fields = json.loads(message.fields)
      self.doc_storage.body = message.body or ''
      self.fields = self.doc_storage.fields
    else:
      raise NotImplementedError()

  def to_message(self):
    message = messages.DocumentMessage()
    message.builtins = messages.BuiltInFieldsMessage()
    message.builtins.title = self.title
    message.basename = self.basename
    message.pod_path = self.pod_path
    message.collection_path = self.collection.collection_path
    message.body = self.body
    message.content = self.content
    message.fields = json.dumps(self.fields, cls=utils.JsonEncoder)
    message.serving_path = self.get_serving_path()
    return message


# TODO(jeremydw): This needs a lot of cleanup. :)

class BaseDocumentStorage(object):

  def __init__(self, pod_path, pod, locale=None, default_locale=None):
    # TODO(jeremydw): Only accept Locale objects, not strings.
    self.default_locale = default_locale
    self.locale = str(locale) if isinstance(locale, basestring) else locale
    self.pod_path = pod_path
    self.pod = pod
    self.content = None
    self.fields = {}
    self.tagged_fields = {}
    self.builtins = None
    self.body = None
    try:
      self.load()
    except IOError:  # Document doesn't exist.
      pass

  def load(self):
    raise NotImplementedError

  def html(self, doc):
    return self.body

  def write(self, content):
    self.content = content
    self.pod.write_file(self.pod_path, content)


class YamlDocumentStorage(BaseDocumentStorage):

  def load(self):
    path = self.pod_path
    content = self.pod.read_file(path)
    fields = utils.parse_yaml(content, path=path, locale=self.locale,
                              default_locale=self.default_locale)
    self.content = None
    self.fields = fields or {}
    self.tagged_fields = {}
    self.body = None
    self.tagged_fields = copy.deepcopy(fields)
    fields = untag_fields(fields, locale=self.locale, pod=self.pod)


class HtmlDocumentStorage(YamlDocumentStorage):
  pass


class MarkdownDocumentStorage(BaseDocumentStorage):

  def load(self):
    path = self.pod_path
    content = self.pod.read_file(path)
    fields, body = utils.parse_markdown(
        content, path=path, locale=self.locale, default_locale=self.default_locale)
    self.content = content
    self.fields = fields or {}
    self.body = body
    self.tagged_fields = copy.deepcopy(fields)
    fields = untag_fields(fields, locale=self.locale, pod=self.pod)

  def html(self, doc):
    val = self.body
    if val is not None:
      extensions = [
        tables.TableExtension(),
        toc.TocExtension(),
        markdown_extensions.CodeBlockExtension(),
        markdown_extensions.IncludeExtension(doc.pod),
        markdown_extensions.UrlExtension(doc.pod),
      ]
      val = markdown.markdown(val.decode('utf-8'), extensions=extensions)
    return val


def untag_fields(fields, locale=None, pod=None):
  """Untags fields, handling translation priority."""
  untagged_keys_to_add = {}
  nodes_and_keys_to_add = []
  nodes_and_keys_to_remove = []
  catalog = pod.catalogs.get(locale)
  def callback(item, key, node):
    if not isinstance(key, basestring):
      return
    if key.endswith('@'):
      untagged_key = key.rstrip('@')
      priority = len(key) - len(untagged_key)
      content = node[key]
      nodes_and_keys_to_remove.append((node, key))
      if priority > 1 and untagged_key in untagged_keys_to_add:
        try:
          has_translation_for_higher_priority_key = content in catalog
        except AttributeError:
          has_translation_for_higher_priority_key = False
        if has_translation_for_higher_priority_key:
          untagged_keys_to_add[untagged_key] = True
          nodes_and_keys_to_add.append((node, untagged_key, content))
      elif priority <= 1:
        untagged_keys_to_add[untagged_key] = True
        nodes_and_keys_to_add.append((node, untagged_key, content))
  utils.walk(fields, callback)
  for node, key in nodes_and_keys_to_remove:
    del node[key]
  for node, untagged_key, content in nodes_and_keys_to_add:
    node[untagged_key] = content
  return fields
