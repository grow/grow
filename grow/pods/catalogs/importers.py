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
    'zh-HK': 'pt_PT',
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

  def import_path(self, path):
    if path.endswith('.zip') and os.path.isfile(path):
      self.import_zip_file(path)
    elif os.path.isdir(path):
      self.import_dir(path)
    else:
      raise Error('Must import a zip file or directory.')

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
      po_path = os.path.join(locale_dir, 'messages.po')
      self.import_file(locale, po_path)

  def import_file(self, locale, po_path):
    if not os.path.exists(po_path):
      raise Error('Couldn\'t find PO file at: {}'.format(po_path))
    babel_locale = external_to_babel_locales.get(locale, locale)
    locale = locale.replace('-', '_')
    pod_translations_dir = os.path.join(self.pod.root, 'translations', babel_locale,
                                        'LC_MESSAGES')
    pod_po_path = os.path.join(pod_translations_dir, 'messages.po')
    _mkdir(pod_translations_dir)
    shutil.copyfile(po_path, pod_po_path)
    self.pod.logger.info('Imported: {}'.format(locale))
