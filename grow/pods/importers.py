import collections
from babel.messages import pofile
import cStringIO
import copy
import errno
import os
import shutil
import tempfile
import zipfile


default_external_to_babel_locales = collections.defaultdict(list)
builtin_locales = {
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
for key, value in builtin_locales.iteritems():
    default_external_to_babel_locales[key].append(value)


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
        if not os.path.exists(po_path):
            raise Error('Couldn\'t find PO file: {}'.format(po_path))
        content = open(po_path).read()
        return self.import_content(locale, content)

    def import_content(self, locale, content):
        if locale is None:
            raise Error('Must specify locale.')

        # Leverage user-defined locale identifiers when importing translations.
        external_to_babel_locales = copy.deepcopy(
            default_external_to_babel_locales)
        if self.pod.podspec.localization:
            if 'import_as' in self.pod.podspec.localization:
                import_as = self.pod.podspec.localization['import_as']
                for external_locale, babel_locales in import_as.iteritems():
                    for babel_locale in babel_locales:
                        external_to_babel_locales[external_locale].append(
                            babel_locale)

        babel_locales = external_to_babel_locales.get(locale, [locale])
        for babel_locale in babel_locales:
          pod_translations_dir = os.path.join(
              'translations', babel_locale, 'LC_MESSAGES')
          pod_po_path = os.path.join(pod_translations_dir, 'messages.po')
          if self.pod.file_exists(pod_po_path):
              existing_po_file = self.pod.open_file(pod_po_path)
              existing_catalog = pofile.read_po(existing_po_file, babel_locale)
              po_file_to_merge = cStringIO.StringIO()
              po_file_to_merge.write(content)
              po_file_to_merge.seek(0)
              catalog_to_merge = pofile.read_po(po_file_to_merge, babel_locale)
              num_imported = 0
              for message in catalog_to_merge:
                  if message.id not in existing_catalog:
                      existing_catalog[message.id] = message
                      num_imported += 1
                  elif (message.string
                        and existing_catalog[message.id].string != message.string):
                      # Avoid overwriting with empty/identical strings.
                      existing_catalog[message.id].string = message.string
                      num_imported += 1
              existing_po_file = self.pod.open_file(pod_po_path, mode='w')
              pofile.write_po(existing_po_file, existing_catalog, width=80,
                              sort_output=True, sort_by_file=True)
              text = 'Updated {} of {} translations: {}'
              message = text.format(num_imported, len(catalog_to_merge), babel_locale)
              self.pod.logger.info(message)
          else:
              self.pod.write_file(pod_po_path, content)
              message = 'Imported new catalog: {}'.format(babel_locale)
              self.pod.logger.info(message)
