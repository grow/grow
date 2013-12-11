from grow.common import utils
from grow.pods.blueprints import documents
from grow.pods.blueprints import messages
import json
import operator
import os


class Error(Exception):
  pass


class BlueprintExistsError(Error):
  pass


class CollectionNotEmptyError(Error):
  pass


class BadBlueprintNameError(Error, ValueError):
  pass


class CollectionDoesNotExistError(Error, ValueError):
  pass


class BadFieldsError(Error, ValueError):
  pass


class Blueprint(object):

  def __init__(self, collection_path, pod):
    utils.validate_name(collection_path)
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

  def exists(self):
    return self.pod.file_exists(self._blueprint_path)

  def create_from_message(self, message):
    if self.exists():
      raise BlueprintExistsError('Blueprint "{}" already exists.'.format(self.collection_path))
    self.update_from_message(message)
    return self

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

  def list_categories(self):
    return self.yaml.get('categories')

  @property
  def title(self):
    return self.yaml.get('title')

  def delete(self):
    if len(self.list_documents(include_hidden=True)):
      text = 'Collections that are not empty cannot be deleted.'
      raise CollectionNotEmptyError(text)
    self.pod.delete_file(self._blueprint_path)

  def update_from_message(self, message):
    if not message.fields:
      raise BadFieldsError('Fields are required to create a collection.')
    fields = json.loads(message.fields)
    fields = utils.dump_yaml(fields)
    self.pod.write_file(self._blueprint_path, fields)

  def get_view(self):
    return self.yaml.get('view')

  def get_path_format(self):
    return self.yaml.get('path')

  def list_documents(self, order_by=None, reverse=None, include_hidden=False):
    if not self.exists():
      raise CollectionDoesNotExistError('Collection "{}" does not exist.'.format(self.collection_path))
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

  def to_message(self):
    message = messages.BlueprintMessage()
    message.title = self.title
    message.collection_path = self.collection_path
    return message
