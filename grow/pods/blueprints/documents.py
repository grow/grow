from grow.common import utils
from grow.pods.blueprints import messages
import json
import markdown
import os


class Document(object):

  def __init__(self, doc_path, pod, blueprint=None, body_format=None):
    self.doc_path = doc_path
    self.pod_path = '/content/{}'.format(doc_path.lstrip('/'))
    self.basename = os.path.basename(doc_path)
    self.slug, self.ext = os.path.splitext(self.basename)

    self.pod = pod
    self.blueprint = blueprint

    self.format = messages.extensions_to_formats.get(self.ext)
    if self.format == messages.Format.MARKDOWN:
      self.doc_storage = MarkdownDocumentStorage(self.pod_path, self.pod)
    elif self.format == messages.Format.YAML:
      self.doc_storage = YamlDocumentStorage(self.pod_path, self.pod)
    else:
      raise NotImplementedError(self.pod_path)

    self.fields = self.doc_storage.fields

  def __repr__(self):
    return '<Document: {}>'.format(self.pod_path)

  @property
  def url(self):
    return self.get_serving_path()

  @property
  def is_hidden(self):
    return bool(self.fields.get('$hidden'))

  @property
  def order(self):
    return self.fields.get('$order')

  @property
  def title(self):
    return self.fields.get('$title')

  @property
  def published(self):
    return self.fields.get('$published')

  def delete(self):
    self.pod.delete_file(self.pod_path)

  def has_blueprint(self):
    return self.blueprint.exists()

  def has_url(self):
    return True

  def get_view(self):
    return self.fields.get('$view', self.blueprint.get_view())

  def get_path_format(self):
    return self.fields.get('$path', self.blueprint.get_path_format())

  def get_serving_path(self):
    path_format = (self.get_path_format()
        .replace('<grow:slug>', '{slug}')
        .replace('<grow:published_year>', '{published_year}'))
    return path_format.format(**{
        'slug': self.slug,
        'published_year': self.published.year if self.published else None,
    })

  @property
  @utils.memoize
  def body(self):
    content = self.doc_storage.body
    return content.decode('utf-8')

  @property
  @utils.memoize
  def content(self):
    content = self.doc_storage.content
    return content.decode('utf-8')

  def __eq__(self, other):
    return (isinstance(self, Document)
            and isinstance(other, Document)
            and self.pod_path == other.pod_path)

#  def __getattr__(self, name):
#    if name in self.fields:
#      return self.fields[name]
##    if '${}'.format(name) in self.yaml:
##      return self.yaml['${}'.format(name)]
#    return object.__getattribute__(self, name)

  def get_next(self):
    docs = self.blueprint.list_servable_documents()
    for i, doc in enumerate(docs):
      if doc == self:
        return docs[i + 1]

  def get_prev(self):
    docs = self.blueprint.list_servable_documents()
    for i, doc in enumerate(docs):
      if doc == self:
        return docs[i - 1]

  def to_message(self):
    message = messages.DocumentMessage()
    message.builtins = messages.BuiltInFieldsMessage()
    message.builtins.title = self.title
    message.basename = self.basename
    message.doc_path = self.doc_path
    message.collection_path = self.blueprint.collection_path
    message.body = self.body
    message.content = self.content
    message.fields = json.dumps(self.fields, cls=utils.JsonEncoder)
    message.html = self.doc_storage.html
    return message

  def create_from_message(self, message):
    self.update_from_message(message)

  def update_from_message(self, message):
    if message.content is not None:
      if isinstance(message.content, unicode):
        content = message.content.encode('utf-8')
      else:
        content = message.content
      self.doc_storage.write(content)
    elif message.body is not None:
      pass


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

  def write(self, content):
    self.pod.write_file(self.pod_path, content)

  @property
  def html(self):
    return self.body

  def save(self):
    pass


class YamlDocumentStorage(BaseDocumentStorage):

  def load(self):
    path = self.pod_path
    content = self.pod.read_file(path)
    fields, body = utils.parse_yaml(content)
    self.content = content
    self.fields = fields or {}
    self.body = body


class MarkdownDocumentStorage(BaseDocumentStorage):

  def load(self):
    path = self.pod_path
    content = self.pod.read_file(path)
    fields, body = utils.parse_markdown(content)
    self.content = content
    self.fields = fields or {}
    self.body = body

  @property
  def html(self):
    val = self.body
    if val is not None:
      val = markdown.markdown(val.decode('utf-8'))
    return val
