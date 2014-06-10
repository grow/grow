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



class Translations(object):

  def __init__(self, pod=None):
    self.pod = pod
    self.root = '/translations'

  def get_translation(self, locale):
    return Translation(pod=self.pod, locale=locale)

  def list_locales(self):
    locales = set()
    for path in self.pod.list_dir(self.root):
      parts = path.split('/')
      if len(parts) > 2:
        locales.add(parts[1])
    return list(locales)

  def recompile_mo_files(self):
    locales = self.list_locales()
    for locale in locales:
      translation = Translation(pod=self.pod, locale=locale)
      if not translation.po_exists():
        logging.info('Catalog for {} does not exist, skipping compilation.'.format(translation))
        continue
      translation.recompile_mo()

  def get_gettext_tanslations(self, locale):
    return self._translations[locale].get_gettext_translations()

  def to_message(self):
    message = messages.TranslationsMessage()
    message.catalogs = []
    for locale in self.list_locales():
      message_ = messages.TranslationCatalogMessage()
      message_.locale = locale
      message.catalogs.append(message_)
    return message

  def get_catalog(self, locale=None):
    path = os.path.join(self.root, 'messages.pot')
    try:
      fp = self.pod.open_file(path)
      return pofile.read_po(fp)
    except IOError:
      text = 'Warning: Message template does not exist: {}'
      logging.warning(text.format(path))

  def init_catalogs(self, locales):
    for locale in locales:
      translation = self.get_translation(locale)
      translation.init_catalog()

  def update_catalogs(self, locales):
    for locale in locales:
      translation = self.get_translation(locale)
      translation.update_catalog()

  def extract(self):
    catalog_obj = catalog.Catalog()

    # Create directory if it doesn't exist. TODO(jeremydw): Optimize this.
    template_path = os.path.join(self.root, 'messages.pot')
    if not self.pod.file_exists(template_path):
      self.pod.create_file(template_path, None)

    template = self.pod.open_file(template_path, mode='w')
    extracted = []

    logging.info('Updating translation template: {}'.format(template_path))

    # Extract messages from views.
    pod_files = self.pod.list_dir('/views/')
    for path in pod_files:
      pod_path = os.path.join('/views', path)
      if os.path.splitext(pod_path)[-1] in _TRANSLATABLE_EXTENSIONS:
        logging.info('Extracting from view: {}'.format(pod_path))
        fp = self.pod.open_file(pod_path)
        try:
          messages = extract.extract('jinja2.ext.babel_extract', fp)
          for message in messages:
            lineno, string, comments, context = message
            added_message = catalog_obj.add(
                string, None, [(pod_path, lineno)], auto_comments=comments,
                context=context)
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


class Translation(object):

  def __init__(self, pod, locale):
    self.pod = pod
    locale_code = str(locale)
    self.locale = locale
    self.path = os.path.join('translations', locale_code)
    try:
      path = os.path.join(self.pod.root, 'translations', locale_code)
      translations = gettext.translation(
          'messages', os.path.dirname(path), [locale_code],
          storage=self.pod.storage)
    except IOError:
      # TODO(jeremydw): If translation mode is strict, raise an error here if
      # no translation file is found.
      translations = gettext.NullTranslations()
    self._gettext_translations = translations

  def __repr__(self):
    return '<Translations: {}>'.format(self.path)

  def to_message(self):
    message = messages.TranslationCatalogMessage()
    message.locale = self.locale
    message.messages = []
    for msgid, msgstr in self.get_catalog().iteritems():
      message_ = messages.MessageMessage()
      message_.msgid = msgid
      message_.msgstr = msgstr
      message.messages.append(message_)
    return message

  def get_gettext_translations(self):
    return self._gettext_translations

  def get_catalog(self):
    return self._gettext_translations._catalog

  def init_catalog(self):
    locale = str(self.locale)
    input_path = os.path.join('translations', 'messages.pot')
    output_path = os.path.join('translations', locale, 'LC_MESSAGES', 'messages.po')
    logging.info('Creating catalog %r based on %r', output_path, input_path)
    infile = self.pod.open_file(input_path)
    try:
      babel_catalog = pofile.read_po(infile, locale=locale)
    finally:
      infile.close()

    babel_locale = babel.Locale.parse(locale)
    babel_catalog.locale = babel_locale
    babel_catalog.revision_date = datetime.now(util.LOCALTZ)
    babel_catalog.fuzzy = False

    # TODO(jeremydw): Optimize.
    # Creates directory if it doesn't exist.
    path = os.path.join(output_path)
    if not self.pod.file_exists(path):
      self.pod.create_file(path, None)

    outfile = self.pod.open_file(output_path, mode='w')
    try:
      pofile.write_po(outfile, babel_catalog, width=80)
    finally:
      outfile.close()

  def update_catalog(self, use_fuzzy=False, ignore_obsolete=True, include_previous=True,
                     width=80):
    locale = str(self.locale)
    domain = 'messages'
    po_filename = os.path.join(self.path, 'LC_MESSAGES', 'messages.po')
    pot_filename = os.path.join('translations', 'messages.pot')
    template = pofile.read_po(self.pod.open_file(pot_filename))

    # Create a catalog if it doesn't exist.
    if not self.pod.file_exists(po_filename):
      self.init_catalog()
      return

    logging.info('Updating catalog {} using {}'.format(po_filename, pot_filename))
    infile = self.pod.open_file(po_filename, 'U')
    try:
      catalog = pofile.read_po(infile, locale=locale, domain=domain)
    finally:
      infile.close()

    catalog.update(template, use_fuzzy)

    temp_filename = po_filename + '.tmp'
    if not self.pod.file_exists(temp_filename):
      self.pod.create_file(temp_filename, None)

    temp_file = self.pod.open_file(temp_filename, 'w')
    try:
      try:
        pofile.write_po(temp_file, catalog, ignore_obsolete=ignore_obsolete,
                        include_previous=include_previous, width=width)
      finally:
        temp_file.close()
    except:
      self.pod.delete_file(temp_filename)
      raise

    self.pod.move_file_to(temp_filename, po_filename)

  def po_exists(self):
    path = os.path.join(self.path, 'LC_MESSAGES', 'messages.po')
    return self.pod.file_exists(path)

  def recompile_mo(self, use_fuzzy=False):
    locale = str(self.locale)
    po_filename = os.path.join(self.path, 'LC_MESSAGES', 'messages.po')
    mo_filename = os.path.join(self.path, 'LC_MESSAGES', 'messages.mo')
    po_file = self.pod.open_file(po_filename)
    try:
      catalog = pofile.read_po(po_file, locale)
    finally:
      po_file.close()

    num_translated = 0
    num_total = 0
    for message in list(catalog)[1:]:
      if message.string:
        num_translated += 1
      num_total += 1

    if catalog.fuzzy and not use_fuzzy:
      logging.info('Catalog {} is marked as fuzzy, skipping.'.format(po_filename))

    try:
      for message, errors in catalog.check():
        for error in errors:
          logging.error('Error: {}:{}: {}'.format(po_filename, message.lineno, error))
    except IOError:
      logging.info('Skipped catalog check.')

    text = 'Compiling {}/{} translated strings to {}'
    logging.info(text.format(num_translated, num_total, mo_filename))

    mo_file = self.pod.open_file(mo_filename, 'w')
    try:
      mofile.write_mo(mo_file, catalog, use_fuzzy=use_fuzzy)
    finally:
      mo_file.close()

  def machine_translate(self):
    locale = str(self.locale)
    domain = 'messages'
    po_filename = os.path.join(self.path, 'LC_MESSAGES', 'messages.po')

    # Create a catalog if it doesn't exist.
    if not self.pod.file_exists(po_filename):
      self.init_catalog()
      return

    infile = self.pod.open_file(po_filename, 'U')
    try:
      catalog = pofile.read_po(infile, locale=locale, domain=domain)
    finally:
      infile.close()

    # Get strings to translate.
    # TODO(jeremydw): Use actual string, not the msgid. Currently we assume
    # the msgid is the source string.
    messages_to_translate = [message for message in catalog if not message.string]
    strings_to_translate = [message.id for message in messages_to_translate]
    if not strings_to_translate:
      logging.info('No untranslated strings for {}, skipping.'.format(locale))
      return

    # Convert Python-format named placeholders to numerical placeholders compatible
    # with Google Translate. Ex: %(name)s => (O).
    placeholders = []  # Lists a mapping of (#) placeholders to %(name)s placeholders.
    for n, string in enumerate(strings_to_translate):
      match = re.search('(%\([^\)]*\)\w)', string)
      if not match:
        placeholders.append(None)
        continue
      for i, group in enumerate(match.groups()):
        num_placeholder = '({})'.format(i)
        nums_to_names = {}
        nums_to_names[num_placeholder] = group
        replaced_string = string.replace(group, num_placeholder)
        placeholders.append(nums_to_names)
        strings_to_translate[n] = replaced_string

    machine_translator = goslate.Goslate()
    results = machine_translator.translate(strings_to_translate, locale)

    for i, string in enumerate(results):
      message = messages_to_translate[i]

      # Replace numerical placeholders with named placeholders.
      if placeholders[i]:
        for num_placeholder, name_placeholder in placeholders[i].iteritems():
          string = string.replace(num_placeholder, name_placeholder)

      message.string = string
      if isinstance(string, unicode):
        string = string.encode('utf-8')
      source = message.id
      source = source.encode('utf-8') if isinstance(source, unicode) else source

    output_path = os.path.join('translations', locale, 'LC_MESSAGES', 'messages.po')
    outfile = self.pod.open_file(output_path, mode='w')
    text = 'Machine translated {} strings: {}'
    logging.info(text.format(len(strings_to_translate), output_path))
    try:
      pofile.write_po(outfile, catalog, width=80)
    finally:
      outfile.close()
