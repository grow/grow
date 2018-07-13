"""Grow translation importers."""

from babel.messages import catalog
from babel.messages import pofile
import cStringIO
import collections
import copy
import csv
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

    def __init__(self, pod, include_obsolete=True):
        self.pod = pod
        self.include_obsolete = include_obsolete

    def _validate_path(self, path):
        if not os.path.isfile(path):
            raise Error('Not found: {}'.format(path))

    def import_path(self, path, locale=None):
        if path.endswith('.zip'):
            self._validate_path(path)
            return self.import_zip_file(path)
        elif path.endswith('.po'):
            self._validate_path(path)
            return self.import_file(locale, path)
        elif os.path.isdir(path):
            return self.import_dir(path)
        elif path.endswith('.csv'):
            return self.import_csv_file(path)
        else:
            raise Error('Must import a .zip, .csv, .po file, or directory.')

    def import_csv_file(self, path):
        """Imports a CSV file formatted with locales in the header row and
        translations in the body rows."""
        default_locale = self.pod.podspec.localization.get('default_locale', 'en')
        locales_to_catalogs = {}
        with open(path) as fp:
            reader = csv.DictReader(fp)
            for row in reader:
                if default_locale not in row:
                    text = 'Locale {} not found in {}'.format(default_locale, path)
                    raise Error(text)
                msgid = row[default_locale]
                for locale, translation in row.iteritems():
                    if locale == default_locale:
                        continue
                    message = catalog.Message(msgid, translation)
                    if locale not in locales_to_catalogs:
                        locales_to_catalogs[locale] = catalog.Catalog()
                    locales_to_catalogs[locale][msgid] = message
        for locale, catalog_obj in locales_to_catalogs.iteritems():
            fp = cStringIO.StringIO()
            pofile.write_po(fp, catalog_obj)
            fp.seek(0)
            content = fp.read()
            self.import_content(locale, content)
            fp.close()

    def import_zip_file(self, zip_path):
        try:
            temp_dir_path = tempfile.mkdtemp()
            with zipfile.ZipFile(zip_path, 'r') as zip_file:
                zip_file.extractall(temp_dir_path)
            return self.import_dir(temp_dir_path)
        finally:
            shutil.rmtree(temp_dir_path)

    def import_dir(self, dir_path):
        # Track if the imported content is actually changing the translations.
        has_changed_content = False

        # Detect whether importing from another pod.
        podspec_path = os.path.join(dir_path, 'podspec.yaml')
        if os.path.exists(podspec_path):
            text = 'Importing from pod -> {}'.format(podspec_path)
            self.pod.logger.info(text)
            translations_dir = os.path.join(dir_path, 'translations')
            for locale in os.listdir(translations_dir):
                po_path = os.path.join(
                        translations_dir, locale, 'LC_MESSAGES', 'messages.po')
                if os.path.exists(po_path):
                    if self.import_file(locale, po_path):
                        has_changed_content = True
            return has_changed_content

        # TODO(jeremydw): Allow a custom syntax for translation importers.
        # Currently, assume one directory per locale.
        for locale in os.listdir(dir_path):
            locale_dir = os.path.join(dir_path, locale)
            if locale.startswith('.') or os.path.isfile(locale_dir):
                continue
            for basename in os.listdir(locale_dir):
                po_path = os.path.join(locale_dir, basename)
                if basename.endswith('.po'):
                    if self.import_file(locale, po_path):
                        has_changed_content = True
                else:
                    self.pod.logger.warning('Skipping: {}'.format(po_path))

        return has_changed_content

    def import_file(self, locale, po_path):
        if not os.path.exists(po_path):
            raise Error('Couldn\'t find PO file: {}'.format(po_path))
        content = open(po_path).read()
        return self.import_content(locale, content)

    def import_content(self, locale, content):
        if locale is None:
            raise Error('Must specify locale.')

        # Track if the imported content is actually changing the translations.
        has_changed_content = False

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
                existing_catalog = pofile.read_po(
                    existing_po_file, babel_locale)
                po_file_to_merge = cStringIO.StringIO()
                po_file_to_merge.write(content)
                po_file_to_merge.seek(0)
                catalog_to_merge = pofile.read_po(
                    po_file_to_merge, babel_locale)
                num_imported = 0
                for message in catalog_to_merge:
                    if message.id not in existing_catalog:
                        # Skip messages that don't exist if we are not
                        # including obsolete messages.
                        if not self.include_obsolete:
                            continue
                        existing_catalog[message.id] = message
                        if message.id:  # Only count the non-header messages.
                            num_imported += 1
                    elif (message.string
                          and existing_catalog[message.id].string != message.string):
                        # Avoid overwriting with empty/identical strings.
                        existing_catalog[message.id].string = message.string
                        num_imported += 1

                if num_imported > 0:
                    has_changed_content = True
                    existing_po_file = self.pod.open_file(pod_po_path, mode='w')
                    pofile.write_po(existing_po_file, existing_catalog, width=80,
                                    sort_output=True, sort_by_file=True)
                    text = 'Updated {} of {} translations: {}'
                    message = text.format(num_imported, len(
                        catalog_to_merge), babel_locale)
                    self.pod.logger.info(message)
                else:
                    text = 'No translations updated: {}'
                    message = text.format(babel_locale)
                    self.pod.logger.info(message)
            else:
                # Skip new catalogs if not including obsolete messages.
                if not self.include_obsolete:
                    continue
                has_changed_content = True
                self.pod.write_file(pod_po_path, content)
                message = 'Imported new catalog: {}'.format(babel_locale)
                self.pod.logger.info(message)

        return has_changed_content
