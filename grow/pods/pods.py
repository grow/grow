import logging
import mimetypes
import os
from grow.common import utils
from grow.pods import files
from grow.pods import locales
from grow.pods import messages
from grow.pods import routes
from grow.pods import storage
from grow.pods import tests
from grow.pods import translations
from grow.pods.blueprints import blueprints

mimetypes.add_type('text/css', '.css')
mimetypes.add_type('image/svg+xml', '.svg')



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

  @property
  @utils.memoize
  def yaml(self):
    return utils.parse_yaml(self.read_file('/pod.yaml'))[0]

  @property
  def flags(self):
    return self.yaml.get('flags', {})

  def list_dir(self, pod_path):
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

  def match(self, path, domain=None, script_name=None, subdomain=None, url_scheme=None):
    if url_scheme is None:
      url_scheme = 'http'
    return self.routes.match(path, domain=domain, script_name=script_name, subdomain=subdomain, url_scheme=url_scheme)

  def export(self):
    if self.tests.exists:
      self.tests.run()
    output = {}
    for path in self.routes.list_concrete_paths():
      try:
        controller = self.match(path)
        output[path] = controller.render()
      except:
        logging.error('Error rendering: {}'.format(path))
        raise
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
