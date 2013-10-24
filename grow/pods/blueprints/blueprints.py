import markdown
import operator
from datetime import date
from datetime import datetime
from datetime import time
import os
from grow.common import utils
from grow.pods.blueprints import messages


class Blueprint(object):

  def __init__(self, nickname, pod):
    self.nickname = nickname
    self.pod = pod
    self.pod_path = '/content/{}'.format(self.nickname)

  @classmethod
  def list(cls, pod):
    paths = pod.list_dir('/content/')
    # TODO: replace with depth
    basenames = set()
    for path in paths:
      basenames.add(path.split('/')[0])
    return [cls(os.path.splitext(basename)[0], pod)
            for basename in basenames]

  @classmethod
  def get(cls, nickname, pod):
    # Instead of nickname, use full pod path.
    return cls(nickname, pod)

  @property
  @utils.memoize
  def yaml(self):
    path = os.path.join(self.pod_path, '_blueprint.yaml')
    return utils.parse_yaml(self.pod.read_file(path))[0]

  def get_document(self, basename):
    return Document(basename, pod=self.pod, blueprint=self)

  def get_view(self):
    return self.yaml.get('view')

  def get_path_format(self):
    return self.yaml.get('path')

  def list_documents(self, order_by=None, reverse=None, include_hidden=False):
    if order_by is None:
      order_by = 'order'
    if reverse is None:
      reverse = False

    paths = self.pod.list_dir(self.pod_path)
    docs = utils.SortedCollection(key=operator.attrgetter(order_by))
    for path in paths:
      basename = os.path.basename(path)
      slug, ext = os.path.splitext(basename)
      if slug.startswith('_') or ext not in messages.extensions_to_formats:
        continue
      doc = self.get_document(basename)
      if not include_hidden and doc.is_hidden:
        continue
      docs.insert(doc)
    return reversed(docs) if reverse else docs

  def list_servable_documents(self, include_hidden=False):
    docs = []
    for doc in self.list_documents(include_hidden=include_hidden):
      if self.yaml.get('draft'):
        continue
      if not doc.has_url() or not doc.get_view():
        continue
      docs.append(doc)
    return docs

  def search(self, order_by='$order'):
    return self.list_documents(order_by=order_by)

  @property
  def num_documents(self):
    return len(self.list_documents())

  def to_message(self):
    message = messages.BlueprintMessage()
    message.nickname = self.nickname
    message.num_documents = self.num_documents
    return message


class Document(object):

  def __init__(self, basename, pod, blueprint=None, body_format=None):
    self.basename = basename
    self.slug, self.ext = os.path.splitext(basename)
    self.pod = pod
    self.blueprint = blueprint
    self.format = messages.extensions_to_formats[self.ext]
    self.pod_path = os.path.join(blueprint.pod_path, basename)
    self._parsed_yaml = None

  def __repr__(self):
    return '<Document: {}>'.format(self.pod_path)

  @classmethod
  def get(cls, pod_path, pod):
    blueprint_path = os.path.dirname(pod_path)
    nickname = os.path.basename(blueprint_path)
    blueprint = Blueprint.get(nickname, pod)
    document_basename = os.path.basename(pod_path)
    return blueprint.get_document(document_basename)

  @property
  def parsed_yaml(self):
    if self._parsed_yaml is None:
      self._parsed_yaml = utils.parse_yaml(self.pod.read_file(self.pod_path))
    return self._parsed_yaml

  @property
  @utils.memoize
  def yaml(self):
    return self.parsed_yaml[0]

  @property
  def url(self):
    return self.get_serving_path()

  @property
  def is_hidden(self):
    return bool(self.yaml.get('$hidden'))

  @property
  def order(self):
    return self.yaml.get('$order')

  @property
  def title(self):
    return self.yaml.get('$title')

  @property
  def published(self):
    return self.yaml.get('$published')

  def has_url(self):
    return True

  def get_view(self):
    return self.yaml.get('$view', self.blueprint.get_view())

  def get_path_format(self):
    return self.yaml.get('$path', self.blueprint.get_path_format())

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
    val = self.parsed_yaml[1]
    if val:
      val = val.decode('utf-8')
      if self.format == messages.Format.MARKDOWN:
        val = markdown.markdown(val)
    return val

  def fields(self):
    return self.yaml

  def __eq__(self, other):
    return isinstance(self, Document) and isinstance(other, Document) and self.pod_path == other.pod_path

  def __getattr__(self, name):
    if name in self.yaml:
      return self.yaml[name]
#    if '${}'.format(name) in self.yaml:
#      return self.yaml['${}'.format(name)]
    return object.__getattribute__(self, name)

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
    message.order = self.order
    message.slug = self.slug
    message.body = self.body
    message.path = self.get_serving_path()
    """
    message.title = self.title
    message.title_nav = self.title_nav
    message.subtitle = self.subtitle
    if self.categories:
      message.categories = self.categories
    if isinstance(self.published, date):
      published = datetime.combine(self.published, time())
    else:
      published = self.published
    message.published = published
    if self.published_by:
      message.published_by = messages.UserMessage()
      message.published_by.name = self.published_by.get('name')
      message.published_by.email = self.published_by.get('email')
      """
    return message



class Index(object):
  pass
