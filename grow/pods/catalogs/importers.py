from babel.messages import pofile
import errno
import os
import shutil
import tempfile
import zipfile


external_to_babel_locales = {
    'en-GB': 'en_GB',
    'es-419': 'es_419',
    'fr-CA': 'fr_CA',
    'iw': 'he_IL',
    'no': 'nb_NO',
    'pt-BR': 'pt_BR',
    'pt-PT': 'pt_PT',
    'zh-CN': 'zh_Hans_CN',
    'zh-HK': 'zh_Hant_HK',
    'zh-TW': 'zh_Hant_TW',
}


def _mkdir(path):
  try:
    os.makedirs(path)
  except OSError as exc:
    if exc.errno == errno.EEXIST and os.path.isdir(path):
      return
    raise


class Error(Exception):
  pass


class Importer(object):

  def __init__(self, pod):
    self.pod = pod

  def _validate_path(self, path):
    if not os.path.isfile(path):
      raise Error('Not found: {}'.format(path))

  def import_path(self, path, locale=None):
    if path.endswith('.zip'):
      self._validate_path(path)
      self.import_zip_file(path)
    elif path.endswith('.po'):
      self._validate_path(path)
      self.import_file(locale, path)
    elif os.path.isdir(path):
      self.import_dir(path)
    else:
      raise Error('Must import a .zip file, .po file, or directory.')

  def import_zip_file(self, zip_path):
    try:
      temp_dir_path = tempfile.mkdtemp()
      with zipfile.ZipFile(zip_path, 'r') as zip_file:
        zip_file.extractall(temp_dir_path)
      self.import_dir(temp_dir_path)
    finally:
      shutil.rmtree(temp_dir_path)

  def import_dir(self, dir_path):
    # TODO(jeremydw): Allow a custom syntax for translation importers.
    # Currently, assume one directory per locale.
    for locale in os.listdir(dir_path):
      locale_dir = os.path.join(dir_path, locale)
      if locale.startswith('.') or os.path.isfile(locale_dir):
        continue
      for basename in os.listdir(locale_dir):
        po_path = os.path.join(locale_dir, basename)
        if basename.endswith('.po'):
          self.import_file(locale, po_path)
        else:
          self.pod.logger.warning('Skipping: {}'.format(po_path))

  def import_file(self, locale, po_path):
    if locale is None:
      raise Error('Must specify locale.')
    if not os.path.exists(po_path):
      raise Error('Couldn\'t find PO file: {}'.format(po_path))
    babel_locale = external_to_babel_locales.get(locale, locale)
    pod_translations_dir = os.path.join('translations', babel_locale, 'LC_MESSAGES')
    pod_po_path = os.path.join(pod_translations_dir, 'messages.po')
    if self.pod.file_exists(pod_po_path):
      existing_po_file = self.pod.open_file(pod_po_path)
      existing_catalog = pofile.read_po(existing_po_file, babel_locale)
      po_file_to_merge = open(po_path)
      catalog_to_merge = pofile.read_po(po_file_to_merge, babel_locale)
      existing_catalog.update(catalog_to_merge)
      existing_po_file = self.pod.open_file(pod_po_path, mode='w')
      pofile.write_po(existing_po_file, catalog_to_merge, width=80)
      self.pod.logger.info(
          'Imported {} translations: {}'.format(len(catalog_to_merge), babel_locale))
    else:
      abs_po_path = self.pod.abs_path(pod_po_path)
      abs_po_dir = os.path.dirname(abs_po_path)
      _mkdir(abs_po_dir)
      shutil.copyfile(po_path, abs_po_path)
      self.pod.logger.info('Imported new catalog: {}'.format(babel_locale))
