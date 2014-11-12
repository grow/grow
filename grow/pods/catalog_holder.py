from . import catalogs
from babel import util
from babel.messages import catalog
from babel.messages import extract
from babel.messages import mofile
from babel.messages import pofile
from datetime import datetime
from grow.common import utils
from grow.pods import messages
from grow.pods.storage import gettext_storage as gettext
import babel
import logging
import os
import re
import tokenize
import goslate


_TRANSLATABLE_EXTENSIONS = (
  '.html',
)

BABEL_CONFIG = os.path.join(os.path.dirname(__file__), 'data', 'babel.cfg')



class Catalogs(object):
  root = '/translations'

  def __init__(self, pod=None):
    self.pod = pod

  def get(self, locale):
    return catalogs.Catalog(pod=self.pod, locale=locale)

  def get_template(self):
    template_path = os.path.join(Catalogs.root, 'messages.pot')
    if not self.pod.file_exists(template_path):
      self.pod.create_file(template_path, None)
    return pofile.read_po(self.pod.open_file(template_path))

  def list_locales(self):
    locales = set()
    for path in self.pod.list_dir(Catalogs.root):
      parts = path.split('/')
      if len(parts) > 2:
        locales.add(parts[1])
    return list(locales)

  def compile(self):
    locales = self.list_locales()
    for locale in locales:
      catalog = self.get(locale)
      if not catalog.exists:
        logging.info('Does not exist: {}'.format(catalog))
        continue
      catalog.compile()

  def to_message(self):
    message = messages.CatalogsMessage()
    message.catalogs = []
    for locale in self.list_locales():
      catalog = self.get(locale)
      message.catalogs.append(catalog.to_message())
    return message

  def init(self, locales):
    for locale in locales:
      catalog = self.get(locale)
      catalog.init()

  def update(self, locales):
    for locale in locales:
      catalog = self.get(locale)
      catalog.update()

  def extract(self):
    # Create directory if it doesn't exist. TODO(jeremydw): Optimize this.
    template_path = os.path.join(Catalogs.root, 'messages.pot')
    if not self.pod.file_exists(template_path):
      self.pod.create_file(template_path, None)
      existing = False
    else:
      existing = pofile.read_po(self.pod.open_file(template_path))

    template = self.pod.open_file(template_path, mode='w')
    catalog_obj = pofile.read_po(self.pod.open_file(template_path))
    extracted = []

    logging.info('Updating translation template: {}'.format(template_path))

    options = {
        'extensions': ','.join(self.pod.get_template_env().extensions.keys()),
        'silent': 'false',
    }

    # Extract messages from content and views.
    pod_files = [os.path.join('/views', path) for path in self.pod.list_dir('/views/')]
    pod_files += [os.path.join('/content', path) for path in self.pod.list_dir('/content/')]
    for pod_path in pod_files:
      if os.path.splitext(pod_path)[-1] in _TRANSLATABLE_EXTENSIONS:
        logging.info('Extracting from: {}'.format(pod_path))
        fp = self.pod.open_file(pod_path)
        try:
          messages = extract.extract('jinja2.ext.babel_extract', fp, options=options)
          for message in messages:
            lineno, string, comments, context = message
            flags = set()
            if existing and string in existing:
              existing_message = existing.get(string)
              if existing_message and 'requested' in existing_message.flags:
                flags.add('requested')
            added_message = catalog_obj.add(
                string, None, [(pod_path, lineno)], auto_comments=comments,
                context=context, flags=flags)
            extracted.append(added_message)
        except tokenize.TokenError:
          logging.error('Problem extracting: {}'.format(pod_path))
          raise

    # Extract messages from content files.
    def callback(doc, item, key, unused_node):
      # Verify that the fields we're extracting are fields for a document that's
      # in the default locale. If not, skip the document.
      _handle_field(doc.pod_path, item, key, unused_node)

    def _handle_field(path, item, key, unused_node):
      if not isinstance(item, basestring):
        return
      if key.endswith('@'):
        comments = []
        context = None
        added_message = catalog_obj.add(
            item, None, [(path, 0)], auto_comments=comments, context=context)
        if added_message not in extracted:
          extracted.append(added_message)

    for collection in self.pod.list_collections():
      logging.info('Extracting from collection: {}'.format(collection.pod_path))
      for doc in collection.list_documents(include_hidden=True):
        utils.walk(doc.tagged_fields, lambda *args: callback(doc, *args))

    # Extract messages from podspec.
    config = self.pod.get_podspec().get_config()
    podspec_path = '/podspec.yaml'
    logging.info('Extracting from podspec: {}'.format(podspec_path))
    utils.walk(config, lambda *args: _handle_field(podspec_path, *args))

    # Write to PO template.
    logging.info('Writing {} messages to translation template.'.format(len(catalog_obj)))
    pofile.write_po(template, catalog_obj, width=80, no_location=True,
                    omit_header=True, sort_output=True, sort_by_file=True)
    template.close()
    return catalog_obj
