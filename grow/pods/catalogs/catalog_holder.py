from . import catalogs
from . import importers
from babel.messages import extract
from babel.messages import pofile
from grow.common import utils
from grow.pods import messages
import os
import tokenize


_TRANSLATABLE_EXTENSIONS = (
  '.html',
  '.md',
  '.yaml',
  '.yml',
)



class Catalogs(object):
  root = '/translations'
  template_path = os.path.join(root, 'messages.pot')

  def __init__(self, pod=None):
    self.pod = pod

  @property
  def exists(self):
    return self.pod.file_exists(Catalogs.template_path)

  def get(self, locale):
    return catalogs.Catalog(pod=self.pod, locale=locale)

  def get_template(self):
    if not self.exists:
      self.pod.create_file(Catalogs.template_path, None)
    return pofile.read_po(self.pod.open_file(Catalogs.template_path))

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
        self.pod.logger.info('Does not exist: {}'.format(catalog))
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

  def import_translations(self, path):
    importer = importers.Importer(self.pod)
    importer.import_path(path)

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

    self.pod.logger.info('Updating translation template: {}'.format(template_path))

    comment_tags = [
        ':',
    ]

    options = {
        'extensions': ','.join(self.pod.get_template_env().extensions.keys()),
        'silent': 'false',
    }

    # Extract messages from content and views.
    pod_files = [os.path.join('/views', path) for path in self.pod.list_dir('/views/')]
    pod_files += [os.path.join('/content', path) for path in self.pod.list_dir('/content/')]
    for pod_path in pod_files:
      if os.path.splitext(pod_path)[-1] in _TRANSLATABLE_EXTENSIONS:
        self.pod.logger.info('Extracting from: {}'.format(pod_path))
        fp = self.pod.open_file(pod_path)
        try:
          messages = extract.extract('jinja2.ext.babel_extract', fp,
                                     options=options, comment_tags=comment_tags)
          for message in messages:
            lineno, string, comments, context = message
            flags = set()
            if existing and string in existing:
              existing_message = existing.get(string)
              if existing_message and 'requested' in existing_message.flags:
                flags.add('requested')
            added_message = catalog_obj.add(
                string, None, auto_comments=comments,
                context=context, flags=flags)
            extracted.append(added_message)
        except tokenize.TokenError:
          self.pod.logger.error('Problem extracting: {}'.format(pod_path))
          raise

    # Extract messages from content files.
    def callback(doc, item, key, unused_node):
      # Verify that the fields we're extracting are fields for a document that's
      # in the default locale. If not, skip the document.
      _handle_field(doc.pod_path, item, key, unused_node)

    def _handle_field(path, item, key, node):
      if not key.endswith('@') or not isinstance(item, basestring):
        return
      # Support gettext "extracted comments" on tagged fields. This is
      # consistent with extracted comments in templates, which follow
      # the format "{#: Extracted comment. #}". An example:
      #   field@: Message.
      #   field@#: Extracted comment for field@.
      auto_comments = []
      if isinstance(node, dict):
        auto_comment = node.get('{}#'.format(key))
        if auto_comment:
          auto_comments.append(auto_comment)
      added_message = catalog_obj.add(item, None, auto_comments=auto_comments)
      if added_message not in extracted:
        extracted.append(added_message)

    for collection in self.pod.list_collections():
      self.pod.logger.info('Extracting from collection: {}'.format(collection.pod_path))
      for doc in collection.list_documents(include_hidden=True):
        utils.walk(doc.tagged_fields, lambda *args: callback(doc, *args))

    # Extract messages from podspec.
    config = self.pod.get_podspec().get_config()
    podspec_path = '/podspec.yaml'
    self.pod.logger.info('Extracting from podspec: {}'.format(podspec_path))
    utils.walk(config, lambda *args: _handle_field(podspec_path, *args))

    # Write to PO template.
    self.pod.logger.info('Writing {} messages to translation template.'.format(len(catalog_obj)))
    pofile.write_po(template, catalog_obj, width=80,
                    omit_header=True, sort_output=True, sort_by_file=True)
    template.close()
    return catalog_obj
