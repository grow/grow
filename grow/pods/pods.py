import logging
import os
import re
from grow.common import utils
from grow.pods import files
from grow.pods import locales
from grow.pods import messages
from grow.pods import routes
from grow.pods import storage
from grow.pods import tests
from grow.pods import translations
from grow.pods.blueprints import blueprints


class Error(Exception):
  pass


class BuildError(Error):
  pass



class Pod(object):

  def __init__(self, root, changeset=None, storage=storage.auto):
    self.storage = storage
    self.root = root if self.storage.is_cloud_storage else os.path.abspath(root)
    self.out_dir = os.path.join(self.root, 'out')
    self.changeset = changeset

    self.routes = routes.Routes(pod=self)
    self.locales = locales.Locales(pod=self)
    self.translations = translations.Translations(pod=self)
    self.tests = tests.Tests(pod=self)

  def __repr__(self):
    if self.changeset is not None:
      return '<Pod: {}@{}>'.format(self.root, self.changeset)
    return '<Pod: {}>'.format(self.root)

  def exists(self):
    return self.file_exists('/podspec.yaml')

  @property
  @utils.memoize
  def yaml(self):
    try:
      return utils.parse_yaml(self.read_file('/podspec.yaml'))[0]
    except IOError:
      raise Error('Pod does not exist or malformed podspec.yaml.')

  @property
  def flags(self):
    return self.yaml.get('flags', {})

  @property
  def title(self):
    return self.yaml.get('title')

  def abs_path(self, pod_path):
    path = os.path.join(self.root, pod_path.lstrip('/'))
    return os.path.join(self.root, path)

  def list_dir(self, pod_path='/'):
    path = os.path.join(self.root, pod_path.lstrip('/'))
    return self.storage.listdir(path)

  def open_file(self, pod_path, mode=None):
    path = os.path.join(self.root, pod_path.lstrip('/'))
    return self.storage.open(path, mode=mode)

  def read_file(self, pod_path):
    path = os.path.join(self.root, pod_path.lstrip('/'))
    return self.storage.read(path)

  def write_file(self, pod_path, content):
    path = os.path.join(self.root, pod_path.lstrip('/'))
    self.storage.write(path, content)

  def file_exists(self, pod_path):
    path = os.path.join(self.root, pod_path.lstrip('/'))
    return self.storage.exists(path)

  def delete_file(self, pod_path):
    path = os.path.join(self.root, pod_path.lstrip('/'))
    return self.storage.delete(path)

  def move_file_to(self, source_pod_path, destination_pod_path):
    source_path = os.path.join(self.root, source_pod_path.lstrip('/'))
    destination_path = os.path.join(self.root, destination_pod_path.lstrip('/'))
    return self.storage.move_to(source_path, destination_path)

  def list_blueprints(self):
    return blueprints.Blueprint.list(self)

  def get_file(self, pod_path):
    return files.File(pod_path, self)

  def get_document(self, doc_path):
    return blueprints.Blueprint.get_document(doc_path, self)

  def get_blueprint(self, collection_path):
    return blueprints.Blueprint.get(collection_path, self)

  def get_translation_catalog(self, locale):
    return self.translations.get_translation(locale)

  def duplicate_to(self, other, exclude=None):
    if not isinstance(other, self.__class__):
      raise ValueError('{} is not a Pod.'.format(other))
    source_paths = self.list_dir('/')
    for path in source_paths:
      if exclude:
        patterns = '|'.join(['({})'.format(pattern) for pattern in exclude])
        if re.match(patterns, path) or 'theme/' in path:
          continue
      content = self.read_file(path)
      other.write_file(path, content)
    # TODO: Handle same-storage copying more elegantly.

  def match(self, path, domain=None, script_name=None, subdomain=None, url_scheme=None):
    if url_scheme is None:
      url_scheme = 'http'
    return self.routes.match(path, domain=domain, script_name=script_name, subdomain=subdomain, url_scheme=url_scheme)

  def export(self):
    if self.tests.exists:
      self.tests.run()
    output = {}
    for path in self.routes.list_concrete_paths():
      controller = self.match(path)
      output[path] = controller.render()
    return output

  def dump(self, suffix='index.html', out_dir=None):
    if out_dir is not None:
      logging.info('Dumping to {}...'.format(out_dir))

    output = self.export()
    clean_output = {}
    if suffix:
      for path, content in output.iteritems():
        if suffix and path.endswith('/') or '.' not in os.path.basename(path):
          path = path.rstrip('/') + '/' + suffix
        clean_output[path] = content
        if out_dir is not None:
          out_path = os.path.join(out_dir, path.lstrip('/'))
          if isinstance(content, unicode):
            content = content.encode('utf-8')
          self.storage.write(out_path, content)
          logging.info('Dumping: {}'.format(path))
    else:
      clean_output = output
    return clean_output

  def to_message(self):
    message = messages.PodMessage()
    message.blueprints = [blueprint.to_message() for blueprint in self.list_blueprints()]
    message.changeset = self.changeset
    message.routes = self.routes.to_message()
    return message

  def delete(self):
    pod_paths = self.list_dir('/')
    for path in pod_paths:
      self.delete_file(path)
    return pod_paths
