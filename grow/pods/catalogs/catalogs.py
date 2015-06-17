from babel import util
from babel.messages import catalog
from babel.messages import mofile
from babel.messages import pofile
from datetime import datetime
from grow.pods import messages
from grow.pods.storage import gettext_storage as gettext
import goslate
import logging
import os
import re



class Catalog(catalog.Catalog):

  def __init__(self, basename='messages.po', locale=None, pod=None):
    self.locale = locale
    self.pod = pod
    if self.locale is None:
      self.pod_path = os.path.join('translations', basename)
      self.is_template = True
    else:
      self.pod_path = os.path.join('translations', str(locale), 'LC_MESSAGES',
                                   basename)
      self.is_template = False
    super(Catalog, self).__init__(locale=self.locale)
    if not self.is_template and self.exists:
      self.load()

  def __repr__(self):
    return '<Catalog: {}>'.format(self.locale)

  def load(self, pod_path=None):
    # Use the "pod_path" argument to load another catalog (such as a template
    # catalog) into this one.
    if pod_path is None:
      pod_path = self.pod_path
    po_file = self.pod.open_file(pod_path)
    try:
      babel_catalog = pofile.read_po(po_file, self.locale)
    finally:
      po_file.close()
    attr_names = [
        '_messages',
        '_num_plurals',
        '_plural_expr',
        'charset',
        'copyright_holder',
        'creation_date',
        'domain',
        'fuzzy',
        'language_team',
        'last_translator',
        'locale',
        'msgid_bugs_address',
        'obsolete',
        'project',
        'revision_date',
        'version',
    ]
    for name in attr_names:
      setattr(self, name, getattr(babel_catalog, name))

  @property
  def exists(self):
    return self.pod.file_exists(self.pod_path)

  @property
  def gettext_translations(self):
    locale = str(self.locale)
    try:
      path = self.pod.abs_path(os.path.join('translations', locale))
      dir_path = os.path.dirname(path)
      translations = gettext.translation('messages', dir_path, [locale],
                                         storage=self.pod.storage)
    except IOError:
      # TODO(jeremydw): If translation mode is strict, raise an error here if
      # no translation file is found.
      translations = gettext.NullTranslations()
    return translations

  def to_message(self):
    catalog_message = messages.CatalogMessage()
    catalog_message.messages = []
    for message in self:
      message_message = messages.MessageMessage()
      message_message.msgid = message.id
      message_message.msgstr = message.string
      catalog_message.messages.append(message_message)
    return catalog_message

  def save(self, ignore_obsolete=True, include_previous=True, width=80):
    if not self.pod.file_exists(self.pod_path):
      self.pod.create_file(self.pod_path, None)
    outfile = self.pod.open_file(self.pod_path, mode='w')
    pofile.write_po(outfile, self, ignore_obsolete=ignore_obsolete,
                    include_previous=include_previous, width=width)
    outfile.close()

  def init(self, template_path):
    self.load(template_path)
    self.revision_date = datetime.now(util.LOCALTZ)
    self.fuzzy = False
    self.save()

  def update(self, template_path=None, use_fuzzy=False, ignore_obsolete=True,
             include_previous=True, width=80):
    """Updates catalog with messages from a template."""
    if template_path is None:
      template_path = os.path.join('translations', 'messages.pot')
    if not self.exists:
      self.init(template_path)
      return
    template_file = self.pod.open_file(template_path)
    template = pofile.read_po(template_file)
    super(Catalog, self).update(template, use_fuzzy)

    # Save the result.
    self.save(ignore_obsolete=ignore_obsolete,
              include_previous=include_previous, width=width)

  def compile(self, use_fuzzy=False):
    mo_dirpath = os.path.dirname(self.pod_path)
    mo_filename = os.path.join(mo_dirpath, 'messages.mo')

    num_translated = 0
    num_total = 0
    for message in list(self)[1:]:
      if message.string:
        num_translated += 1
      num_total += 1

    try:
      for message, errors in self.check():
        for error in errors:
          logging.error('Error: {}:{}: {}'.format(self.locale, message.lineno, error))
    except IOError:
      logging.info('Skipped catalog check for: {}'.format(self))

    text = 'Compiled: {} ({}/{})'
    self.pod.logger.info(text.format(self.locale, num_translated, num_total))

    mo_file = self.pod.open_file(mo_filename, 'w')
    try:
      mofile.write_mo(mo_file, self, use_fuzzy=use_fuzzy)
    finally:
      mo_file.close()

  def machine_translate(self):
    locale = str(self.locale)
    domain = 'messages'
    infile = self.pod.open_file(self.pod_path, 'U')
    try:
      babel_catalog = pofile.read_po(infile, locale=locale, domain=domain)
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

    outfile = self.pod.open_file(self.pod_path, mode='w')
    try:
      pofile.write_po(outfile, babel_catalog, width=80)
    finally:
      outfile.close()
    text = 'Machine translated {} strings: {}'
    logging.info(text.format(len(strings_to_translate), self.pod_path))

  def list_missing(self):
    missing = []
    for message in self:
      if not message.string:
        missing.append(message)
    return missing
