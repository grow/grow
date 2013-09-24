import logging
import os
from grow.pods import messages
from grow.pods.storage import gettext_storage as gettext
from babel.messages import catalog
from babel.messages import extract
from babel.messages import mofile
from babel.messages import pofile


_TRANSLATABLE_EXTENSIONS = (
  '.html',
)



class Translations(object):

  def __init__(self, pod=None):
    self.pod = pod
    self.root = os.path.join(self.pod.root, 'translations')

  def get_translation(self, locale):
    return Translation(pod=self.pod, locale=locale)

  def list_locales(self):
    for _, dirs, _ in os.walk(self.root):
      return dirs

  def recompile_mo_files(self):
    for locale in self.list_locales():
      translation = Translation(pod=self.pod, locale=locale)
      translation.recompile_mo()

  def get_gettext_tanslations(self, locale):
    return self._translations[locale].get_gettext_translations()

  def to_message(self):
    message = messages.TranslationsMessage()
    return message

  def extract(self):
    pot_filename = os.path.join(self.root, 'messages.pot')
    extracted = []
    for pod_path in self.pod.list_dir('/'):
      if os.path.splitext(pod_path)[-1] in _TRANSLATABLE_EXTENSIONS:
        path = self.pod.root + pod_path
#        file_obj = self.pod.storage.open(path)
#        messages = extract.extract('python', file_obj)
#        print messages



class Translation(object):

  def __init__(self, pod, locale):
    self.pod = pod
    self.locale = locale
    self.path = os.path.join(self.pod.root, 'translations', locale)

    try:
      translations = gettext.translation(
          'messages', os.path.dirname(self.path), languages=[self.locale],
          storage=self.pod.storage)
    except IOError:
      translations = gettext.NullTranslations()
    self._gettext_translations = translations

  def to_message(self):
    message = messages.TranslationMessage()
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

  def recompile_mo(self, use_fuzzy=False):
    locale = self.locale
    po_filename = os.path.join(self.path, 'LC_MESSAGES', 'messages.po')
    mo_filename = os.path.join(self.path, 'LC_MESSAGES', 'messages.mo')
    po_file = self.pod.storage.open(po_filename, 'r')
    try:
      catalog = pofile.read_po(po_file, locale)
    finally:
      po_file.close()

    num_translated = 0
    for message in list(catalog)[1:]:
      if message.string:
        num_translated += 1
      percentage = 0
      if len(catalog):
        percentage = num_translated * 100 // len(catalog)
      logging.info(
          '{} of {} messages ({}%) translated in {} so far.'.format(
              num_translated, len(catalog), percentage, po_filename))

    if catalog.fuzzy and not use_fuzzy:
      logging.info('Catalog {} is marked as fuzzy, skipping.'.format(po_filename))

    try:
      for message, errors in catalog.check():
        for error in errors:
          logging.error(
              'Error: {}:{}: {}'.format(
                  po_filename, message.lineno, error))
    except IOError:
      logging.info('Skipped catalog check.')

    logging.info('Compiling catalog {} to {}'.format(po_filename, mo_filename))

    mo_file = self.pod.storage.open(mo_filename, 'w')
    try:
      mofile.write_mo(mo_file, catalog, use_fuzzy=use_fuzzy)
    finally:
      mo_file.close()
