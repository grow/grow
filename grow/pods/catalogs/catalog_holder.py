from . import catalogs
from . import importers
from babel import util as babel_util
from babel.messages import catalog
from babel.messages import extract
from babel.messages import pofile
from grow.common import utils
from grow.pods import messages
import collections
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

  def __init__(self, pod, template_path=None):
    self.pod = pod
    if template_path:
      self.template_path = template_path
    else:
      self.template_path = os.path.join(Catalogs.root, 'messages.pot')

  def get(self, locale, basename='messages.po'):
    return catalogs.Catalog(basename, locale, pod=self.pod)

  def get_template(self, basename='messages.pot'):
    return catalogs.Catalog(basename, None, pod=self.pod)

  def list_locales(self):
    locales = set()
    for path in self.pod.list_dir(Catalogs.root):
      parts = path.split('/')
      if len(parts) > 2:
        locales.add(parts[1])
    return list(locales)

  def __iter__(self):
    for locale in self.list_locales():
      yield self.get(locale)

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

  def init(self, locales, include_header=False):
    for locale in locales:
      catalog = self.get(locale)
      catalog.init(template_path=self.template_path,
                   include_header=include_header)

  def update(self, locales, use_fuzzy=False, include_header=False):
    for locale in locales:
      catalog = self.get(locale)
      self.pod.logger.info('Updating: {}'.format(locale))
      catalog.update(template_path=self.template_path, use_fuzzy=use_fuzzy,
                     include_header=include_header)

  def import_translations(self, path, locale=None):
    importer = importers.Importer(self.pod)
    importer.import_path(path, locale=locale)

  def extract_missing(self, locales, out_path, use_fuzzy=False, paths=None,
                      include_header=False):
    messages_to_locales = collections.defaultdict(list)
    for locale in locales:
      catalog = self.get(locale)
      missing_messages = catalog.list_missing(use_fuzzy=use_fuzzy, paths=paths)
      text = 'Extracted missing strings: {} ({}/{})'
      num_missing = len(missing_messages)
      num_total = len(catalog)
      self.pod.logger.info(text.format(catalog.locale, num_missing, num_total))
      for message in missing_messages:
        messages_to_locales[message].append(catalog.locale)
    self.pod.create_file(out_path, None)
    babel_catalog = pofile.read_po(self.pod.open_file(out_path))
    for message in messages_to_locales.keys():
      babel_catalog[message.id] = message
    self.write_template(out_path, babel_catalog, include_header=include_header)

  def _get_or_create_catalog(self, template_path):
    exists = True
    if not self.pod.file_exists(template_path):
      self.pod.create_file(template_path, None)
      exists = False
    catalog = pofile.read_po(self.pod.open_file(template_path))
    return catalog, exists

  def _add_message(self, catalog, message):
    lineno, string, comments, context = message
    flags = set()
    if string in catalog:
      existing_message = catalog.get(string)
      flags = existing_message.flags
    return catalog.add(string, None, auto_comments=comments, context=context,
                       flags=flags)

  def _should_extract(self, given_paths, path):
    if os.path.splitext(path)[-1] not in _TRANSLATABLE_EXTENSIONS:
      return False
    return not given_paths or path in given_paths

  def extract(self, include_obsolete=False, localized=False, paths=None,
              include_header=False):
    env = self.pod.create_template_env()

    all_locales = set(list(self.pod.list_locales()))
    message_ids_to_messages = {}
    paths_to_messages = collections.defaultdict(set)
    paths_to_locales = collections.defaultdict(set)

    comment_tags = [
        ':',
    ]
    options = {
        'extensions': ','.join(env.extensions.keys()),
        'silent': 'false',
    }

    # Extract messages from content files.
    def callback(doc, item, key, unused_node):
      # Verify that the fields we're extracting are fields for a document
      # that's in the default locale. If not, skip the document.
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
      locations = [(path, 0)]
      existing_message = message_ids_to_messages.get(item)
      if existing_message:
        message_ids_to_messages[item].locations.extend(locations)
        paths_to_messages[path].add(existing_message)
      else:
        message = catalog.Message(item, None, auto_comments=auto_comments,
                                  locations=locations)
        message_ids_to_messages[message.id] = message
        paths_to_messages[path].add(message)

    for collection in self.pod.list_collections():
      text = 'Extracting collection: {}'.format(collection.pod_path)
      self.pod.logger.info(text)
      for doc in collection.list_docs(include_hidden=True):
        if not self._should_extract(paths, doc.pod_path):
          continue
        tagged_fields = doc.get_tagged_fields()
        utils.walk(tagged_fields, lambda *args: callback(doc, *args))
        paths_to_locales[doc.pod_path].update(doc.locales)
        all_locales.update(doc.locales)

    # Extract messages from podspec.
    config = self.pod.get_podspec().get_config()
    podspec_path = '/podspec.yaml'
    if self._should_extract(paths, podspec_path):
      self.pod.logger.info('Extracting podspec: {}'.format(podspec_path))
      utils.walk(config, lambda *args: _handle_field(podspec_path, *args))

    # Extract messages from content and views.
    pod_files = [os.path.join('/views', path)
                 for path in self.pod.list_dir('/views/')]
    pod_files += [os.path.join('/content', path)
                  for path in self.pod.list_dir('/content/')]
    for pod_path in pod_files:
      if self._should_extract(paths, pod_path):
        locales = paths_to_locales.get(pod_path)
        if locales:
          text = 'Extracting: {} ({} locales)'.format(pod_path, len(locales))
          self.pod.logger.info(text)
        else:
          self.pod.logger.info('Extracting: {}'.format(pod_path))
        fp = self.pod.open_file(pod_path)
        try:
          all_parts = extract.extract(
              'jinja2.ext.babel_extract', fp, options=options,
              comment_tags=comment_tags)
          for parts in all_parts:
            lineno, string, comments, context = parts
            locations = [(pod_path, lineno)]
            existing_message = message_ids_to_messages.get(string)
            if existing_message:
              message_ids_to_messages[string].locations.extend(locations)
            else:
              message = catalog.Message(string, None, auto_comments=comments,
                                        context=context, locations=locations)
              paths_to_messages[pod_path].add(message)
              message_ids_to_messages[message.id] = message
        except tokenize.TokenError:
          self.pod.logger.error('Problem extracting: {}'.format(pod_path))
          raise

    # Localized message catalogs.
    if localized:
      for locale in all_locales:
        localized_catalog = self.get(locale)
        if not include_obsolete:
          localized_catalog.obsolete = babel_util.odict()
          for message in list(localized_catalog):
            if message.id not in message_ids_to_messages:
              localized_catalog.delete(message.id, context=message.context)
        for path, message_items in paths_to_messages.iteritems():
          locales_with_this_path = paths_to_locales.get(path)
          if locales_with_this_path and locale not in locales_with_this_path:
            continue
          for message in message_items:
            translation = None
            existing_message = localized_catalog.get(message.id)
            if existing_message:
              translation = existing_message.string
            localized_catalog.add(
                message.id, translation, locations=message.locations,
                auto_comments=message.auto_comments)
        localized_catalog.save(include_header=include_header)
        missing = localized_catalog.list_missing(use_fuzzy=True, paths=paths)
        num_messages = len(localized_catalog)
        num_translated = num_messages - len(missing)
        text = 'Saved: /{} ({}/{})'
        self.pod.logger.info(
            text.format(localized_catalog.pod_path, num_translated,
                        num_messages))
      return

    # Global message catalog.
    template_path = self.template_path
    catalog_obj, _ = self._get_or_create_catalog(template_path)
    if not include_obsolete:
      catalog_obj.obsolete = babel_util.odict()
      for message in list(catalog_obj):
        catalog_obj.delete(message.id, context=message.context)
    for message in message_ids_to_messages.itervalues():
      catalog_obj.add(message.id, None, locations=message.locations,
                      auto_comments=message.auto_comments)
    return self.write_template(
        template_path, catalog_obj, include_obsolete=include_obsolete,
        include_header=include_header)

  def write_template(self, template_path, catalog, include_obsolete=False,
                     include_header=False):
    template_file = self.pod.open_file(template_path, mode='w')
    pofile.write_po(
        template_file, catalog, width=80, omit_header=(not include_header),
        sort_output=True, sort_by_file=True,
        ignore_obsolete=(not include_obsolete))
    text = 'Saved: {} ({} messages)'
    self.pod.logger.info(text.format(template_path, len(catalog)))
    template_file.close()
    return catalog
