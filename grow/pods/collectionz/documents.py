from grow.common import utils
from grow.pods import urls
from grow.pods.collectionz import messages
import json
import logging
import markdown
import os


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
    self.locale = locale
    self.pod_path = pod_path
    self.basename = os.path.basename(pod_path)
    self._slug_clean, self.ext = os.path.splitext(self.basename)

    self.pod = _pod
    self.collection = _collection

    self.format = messages.extensions_to_formats.get(self.ext)
    if self.format == messages.Format.MARKDOWN:
      self.doc_storage = MarkdownDocumentStorage(self.pod_path, self.pod)
    elif self.format == messages.Format.YAML:
      self.doc_storage = YamlDocumentStorage(self.pod_path, self.pod)
    else:
      formats = messages.extensions_to_formats.keys()
      text = 'Basename "{}" does not have a valid extension. Valid formats are: {}'
      raise BadFormatError(text.format(self.basename, ', '.join(formats)))

    self.fields = self.doc_storage.fields

  def __repr__(self):
    if self.locale:
      return "<Document({}, locale='{}')>".format(self.pod_path, self.locale)
    return "<Document({})>".format(self.pod_path)

  @property
  def url(self):
    path = self.get_serving_path()
    return urls.Url(path=path) if path else None

  @property
  def slug(self):
    if self.parent:
      return '/{}/{}/'.format(self.parent.slug, self._slug_clean)
    return self._slug_clean

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
    return self.fields.get('$titles', {}).get(title_name, self.title)

  @property
  def published(self):
    return self.fields.get('$published')

  @property
  def category(self):
    return self.fields.get('$category')

  def delete(self):
    self.pod.delete_file(self.pod_path)

  def exists(self):
    return self.pod.file_exists(self.pod_path)

  def has_collection(self):
    return self.collection.exists()

  def has_url(self):
    return True

  def get_view(self):
    return self.fields.get('$view', self.collection.get_view())

  def get_path_format(self):
    val = None
    if self.locale:
      if '$localization' in self.fields and self.fields['$localization']['path']:
        val = self.fields['$localization']['path']
      else:
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
    path_format = (self.get_path_format()
        .replace('<grow:locale>', '{locale}')
        .replace('<grow:locale>', '{locale}')
        .replace('<grow:slug>', '{slug}')
        .replace('<grow:published_year>', '{published_year}'))
    try:
      return path_format.format(**{
          'parent': self.parent if self.parent else DummyDict(),
          'locale': self.locale,
          'podspec': self.pod.get_podspec(),
          'self': self,
          'slug': self.slug,
      }).replace('//', '/')
    except KeyError:
      logging.error('Error with path format: {}'.format(path_format))
      raise

  def list_locales(self):
    if '$localization' in self.fields:
      if self.fields['$localization'].get('use_podspec_locales'):
        return self.pod.list_locales()
      return self.fields['$localization']['locales']
    return self.collection.list_locales()

  @property
  @utils.memoize
  def body(self):
    content = self.doc_storage.body
    return content.decode('utf-8')

  @property
  def content(self):
    content = self.doc_storage.content
    return content.decode('utf-8')

  @property
  def html(self):
    return self.doc_storage.html

  def __eq__(self, other):
    return (isinstance(self, Document)
            and isinstance(other, Document)
            and self.pod_path == other.pod_path)

  def __getattr__(self, name):
    if name in self.fields:
      return self.fields[name]
    return object.__getattribute__(self, name)

  def get_next(self):
    docs = self.collection.list_servable_documents()
    for i, doc in enumerate(docs):
      if doc == self:
        n = i + 1
        if n == len(docs):
          return None
        return docs[i + 1]

  def get_prev(self):
    docs = self.collection.list_servable_documents()
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
    message.html = self.doc_storage.html
    message.serving_path = self.get_serving_path()
    return message


class BaseDocumentStorage(object):

  def __init__(self, pod_path, pod):
    self.pod_path = pod_path
    self.pod = pod
    self.content = None
    self.fields = {}
    self.builtins = None
    self.body = None
    try:
      self.load()
    except IOError:  # Document doesn't exist.
      pass

  def load(self):
    raise NotImplementedError

  @property
  def html(self):
    return self.body

  def write(self, content):
    self.content = content
    self.pod.write_file(self.pod_path, content)


class YamlDocumentStorage(BaseDocumentStorage):

  def load(self):
    path = self.pod_path
    content = self.pod.read_file(path)
    fields, body = utils.parse_yaml(content, path=path)
    self.content = content
    self.fields = fields or {}
    self.body = body


class MarkdownDocumentStorage(BaseDocumentStorage):

  def load(self):
    path = self.pod_path
    content = self.pod.read_file(path)
    fields, body = utils.parse_markdown(content, path=path)
    self.content = content
    self.fields = fields or {}
    self.body = body

  @property
  def html(self):
    val = self.body
    if val is not None:
      extensions = [
        'toc',
      ]
      val = markdown.markdown(val.decode('utf-8'), extensions=extensions)
    return val
