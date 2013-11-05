from grow.common import utils
from grow.pods.blueprints import documents
from grow.pods.blueprints import messages
import operator
import os


class Blueprint(object):

  def __init__(self, collection_path, pod):
    self.pod = pod
    self.collection_path = collection_path.lstrip('/')
    self.pod_path = '/content/{}'.format(self.collection_path)
    self._blueprint_path = os.path.join(self.pod_path, '_blueprint.yaml')

  @classmethod
  def list(cls, pod):
    paths = pod.list_dir('/content/')
    # TODO: replace with depth
    basenames = set()
    for path in paths:
      parts = path.split('/')
      if len(parts) >= 2:  # Disallow files in root-level /content/ dir.
        basenames.add(parts[0])
    return [cls(os.path.splitext(basename)[0], pod)
            for basename in basenames]

  @classmethod
  def get(cls, collection_path, pod):
    return cls(collection_path, pod)

  @classmethod
  def get_document(cls, doc_path, pod):
    blueprint_doc_path = os.path.dirname(doc_path)
    blueprint = cls.get(blueprint_doc_path, pod)
    return documents.Document(doc_path, pod=pod, blueprint=blueprint)

  @property
  @utils.memoize
  def yaml(self):
    return utils.parse_yaml(self.pod.read_file(self._blueprint_path))[0]

  @property
  def title(self):
    return self.yaml.get('title')

  def exists(self):
    return self.pod.file_exists(self._blueprint_path)

  def get_view(self):
    return self.yaml.get('view')

  def get_path_format(self):
    return self.yaml.get('path')

  def list_documents(self, order_by=None, reverse=None, include_hidden=False):
    if not self.exists():
      return []
    if order_by is None:
      order_by = 'order'
    if reverse is None:
      reverse = False

    paths = self.pod.list_dir(self.pod_path)
    docs = utils.SortedCollection(key=operator.attrgetter(order_by))
    for path in paths:
      full_path = os.path.join(self.pod_path, path.strip('/'))
      doc_path = full_path.replace('/content/', '')
      slug, ext = os.path.splitext(os.path.basename(doc_path))
      if (slug.startswith('_')
          or ext not in messages.extensions_to_formats
          or not doc_path):
        continue
      doc = documents.Document(doc_path, pod=self.pod, blueprint=self)
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

  def search_documents(self, order_by='order'):
    return self.list_documents(order_by=order_by)

  @property
  def num_documents(self):
    return len(self.list_documents())

  def to_message(self):
    message = messages.BlueprintMessage()
    message.title = self.title
    message.collection_path = self.collection_path
    message.num_documents = self.num_documents
    return message
