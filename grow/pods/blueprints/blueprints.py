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
    return cls(nickname, pod)

  @property
  @utils.memoize
  def yaml(self):
    path = os.path.join(self.pod_path, '_blueprint.yaml')
    return utils.parse_yaml(self.pod.read_file(path))[0]

  def get_view(self):
    return self.yaml.get('view')

  def get_path_format(self):
    return self.yaml.get('path')

  def list_documents(self, order_by='order', reverse=False):
    paths = self.pod.list_dir(self.pod_path)
    docs = utils.SortedCollection(key=operator.attrgetter(order_by))
    for path in paths:
      slug, ext = os.path.splitext(os.path.basename(path))
      if slug.startswith('_') or ext != '.yaml':
        continue
      doc = Document(slug, pod=self.pod, blueprint=self)
      docs.insert(doc)
    return reversed(docs) if reverse else docs

  def list_servable_documents(self):
    docs = []
    for doc in self.list_documents():
      if not doc.has_url() or not doc.get_view():
        continue
      docs.append(doc)
    return docs

  def search(self, order_by='order'):
    return self.list_documents(order_by=order_by)

  def to_message(self):
    message = messages.BlueprintMessage()
    return message


class Document(object):

  def __init__(self, slug, pod, blueprint=None):
    self.slug = slug
    self.pod = pod
    self.blueprint = blueprint
    self.pod_path = os.path.join(blueprint.pod_path, '{}.yaml'.format(slug))
    self._parsed_yaml = None

  def __repr__(self):
    return '<Document: {}>'.format(self.pod_path)

  @property
  def parsed_yaml(self):
    if self._parsed_yaml is None:
      self._parsed_yaml = utils.parse_yaml(self.pod.read_file(self.pod_path))
    return self._parsed_yaml

  @property
  @utils.memoize
  def yaml(self):
    return self.parsed_yaml[0]

  def has_url(self):
    return True

  def get_view(self):
    return self.yaml.get('view', self.blueprint.get_view())

  def get_path_format(self):
    return self.yaml.get('path', self.blueprint.get_path_format())

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
      return val.decode('utf-8')

  @property
  def order(self):
    return self.yaml.get('order')

  @property
  def title(self):
    return self.yaml.get('title')

  @property
  @utils.memoize
  def published(self):
    return self.yaml.get('published')

  @property
  def published_by(self):
    return self.yaml.get('published_by')

  @property
  def title_nav(self):
    return self.yaml.get('title_nav', self.title)

  @property
  def subtitle(self):
    return self.yaml.get('subtitle')

  @property
  def categories(self):
    return self.yaml.get('categories')

  def to_message(self):
    message = messages.DocumentMessage()
    message.order = self.order
    message.slug = self.slug
    message.body = self.body
    message.path = self.get_serving_path()
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
    return message
