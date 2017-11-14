"""Base translators for translating Grow content."""

import copy
import json
import logging
import os
import threading
import progressbar
import texttable
import yaml
from protorpc import message_types
from protorpc import messages
from protorpc import protojson
from grow.common import progressbar_non
from grow.common import utils
from grow.translators import errors as translator_errors


class TranslatorStat(messages.Message):
    lang = messages.StringField(1)
    num_words = messages.IntegerField(2)
    num_words_translated = messages.IntegerField(3)
    source_lang = messages.StringField(4)
    ident = messages.StringField(5)
    url = messages.StringField(6)
    uploaded = message_types.DateTimeField(7)
    service = messages.StringField(8)
    downloaded = message_types.DateTimeField(9)


def translator_stat_representer(dumper, stat):
    content = json.loads(protojson.encode_message(stat))
    content.pop('lang')  # Exclude from serialization.
    return dumper.represent_mapping('tag:yaml.org,2002:map', content)


yaml.SafeDumper.add_representer(TranslatorStat,
                                translator_stat_representer)


class TranslatorServiceError(Exception):

    def __init__(self, message, ident=None, locale=None):
        if locale:
            new_message = 'Error for locale "{}" -> {}'.format(locale, message)
        elif ident:
            new_message = 'Error for resource "{}" -> {}'.format(
                ident, message)
        else:
            new_message = message
        super(TranslatorServiceError, self).__init__(new_message)


class Translator(object):
    TRANSLATOR_STATS_PATH = '/translators.yaml'
    KIND = None
    has_immutable_translation_resources = False
    has_multiple_langs_in_one_resource = False

    def __init__(self, pod, config=None, project_title=None,
                 instructions=None, inject=False):
        self.pod = pod
        self.config = config or {}
        self.project_title = project_title or 'Untitled Grow Website'
        self.instructions = instructions
        self._inject = inject

    def _cleanup_locales(self, locales):
        """Certain locales should be ignored."""
        clean_locales = []
        default_locale = self.pod.podspec.default_locale
        skipped = {
            'symlink': set(),
            'po': set(),
        }
        for locale in locales:
            locale_path = os.path.join('translations', str(locale))

            # Silently ignore the default locale.
            if default_locale and str(locale) == str(default_locale):
                continue

            # Ignore the symlinks.
            if os.path.islink(locale_path):
                skipped['symlink'].add(str(locale))
                continue

            # Ignore the locales without a `.PO` file.
            po_path = os.path.join(locale_path, 'LC_MESSAGES', 'messages.po')
            if not self.pod.file_exists(po_path):
                skipped['po'].add(str(locale))
                continue

            clean_locales.append(locale)

        # Summary of skipped files.
        if skipped['symlink']:
            self.pod.logger.info('Skipping: {} (symlinked)'.format(
                ', '.join(sorted(skipped['symlink']))))
        if skipped['po']:
            self.pod.logger.info('Skipping: {} (no `.po` file)'.format(
                ', '.join(sorted(skipped['po']))))

        return clean_locales

    def _download_content(self, stat):
        raise NotImplementedError

    def _upload_catalog(self, catalog, source_lang, prune):
        raise NotImplementedError

    def _upload_catalogs(self, catalogs, source_lang, prune=False):
        raise NotImplementedError

    def _update_acl(self, stat, locale):
        raise NotImplementedError

    def _update_acls(self, stat, locales):
        raise NotImplementedError

    def _update_meta(self, stat, locale, catalog):
        raise NotImplementedError

    def _get_stats_to_download(self, locales):
        # 'stats' maps the service name to a mapping of languages to stats.
        if not self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH):
            return {}
        stats = self.pod.read_yaml(Translator.TRANSLATOR_STATS_PATH)
        if self.KIND not in stats:
            self.pod.logger.info(
                'Nothing found to download from {}'.format(self.KIND))
            return {}
        stats_to_download = stats[self.KIND]
        if locales:
            stats_to_download = dict([(lang, stat)
                                      for (lang, stat) in stats_to_download.iteritems()
                                      if lang in locales])
        for lang, stat in stats_to_download.iteritems():
            if isinstance(stat, TranslatorStat):
                stat = json.loads(protojson.encode_message(stat))
            stat['lang'] = lang
            stat_message = protojson.decode_message(TranslatorStat, json.dumps(stat))
            stats_to_download[lang] = stat_message
        return stats_to_download

    def download(self, locales, save_stats=True, inject=False, include_obsolete=False):
        # TODO: Rename to `download_and_import`.
        if not self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH):
            text = 'File {} not found. Nothing to download.'
            self.pod.logger.info(text.format(Translator.TRANSLATOR_STATS_PATH))
            return
        stats_to_download = self._get_stats_to_download(locales)
        if not stats_to_download:
            return
        num_files = len(stats_to_download)
        text = 'Downloading translations: %(value)d/{} (in %(time_elapsed).9s)'
        widgets = [progressbar.FormatLabel(text.format(num_files))]
        if not inject:
            bar = progressbar_non.create_progressbar(
                "Downloading translations...", widgets=widgets, max_value=num_files)
            bar.start()
        threads = []
        langs_to_translations = {}
        new_stats = []

        def _do_download(lang, stat):
            try:
                new_stat, content = self._download_content(stat)
            except translator_errors.NotFoundError:
                text = 'No translations to download for: {}'
                self.pod.logger.info(text.format(lang))
                return

            new_stat.uploaded = stat.uploaded  # Preserve uploaded field.
            langs_to_translations[lang] = content
            new_stats.append(new_stat)
        for i, (lang, stat) in enumerate(stats_to_download.iteritems()):
            if inject:
                thread = threading.Thread(
                    target=_do_download, args=(lang, stat))
            else:
                thread = utils.ProgressBarThread(
                    bar, True, target=_do_download, args=(lang, stat))
            threads.append(thread)
            thread.start()
            # Perform the first operation synchronously to avoid oauth2 refresh
            # locking issues.
            if i == 0:
                thread.join()
        for i, thread in enumerate(threads):
            if i > 0:
                thread.join()
        if not inject:
            bar.finish()

        has_changed_content = False
        for lang, translations in langs_to_translations.iteritems():
            if inject:
                if self.pod.catalogs.inject_translations(locale=lang, content=translations):
                    has_changed_content = True
            elif self.pod.catalogs.import_translations(
                    locale=lang, content=translations,
                    include_obsolete=include_obsolete):
                has_changed_content = True

        if save_stats and has_changed_content:
            self.save_stats(new_stats)
        return new_stats

    def update_acl(self, locales=None):
        locales = locales or self.pod.catalogs.list_locales()
        locales = self._cleanup_locales(locales)
        if not locales:
            self.pod.logger.info('No locales to found to update.')
            return
        stats_to_download = self._get_stats_to_download(locales)
        if not stats_to_download:
            self.pod.logger.info('No documents found to update.')
            return
        if self.has_multiple_langs_in_one_resource:
            self._update_acls(stats_to_download, locales)
            stat = stats_to_download.values()[0]
            self.pod.logger.info('ACL updated -> {}'.format(stat.ident))
            return
        threads = []
        for i, (locale, stat) in enumerate(stats_to_download.iteritems()):
            thread = threading.Thread(
                target=self._update_acl, args=(stat, locale))
            threads.append(thread)
            thread.start()
            if i == 0:
                thread.join()
            self.pod.logger.info(
                'ACL updated ({}): {}'.format(stat.lang, stat.url))
        for i, thread in enumerate(threads):
            if i > 0:
                thread.join()

    def update_meta(self, locales=None):
        locales = locales or self.pod.catalogs.list_locales()
        locales = self._cleanup_locales(locales)
        if not locales:
            self.pod.logger.info('No locales to found to update.')
            return
        stats_to_download = self._get_stats_to_download(locales)
        if not stats_to_download:
            self.pod.logger.info('No documents found to update.')
            return
        threads = []
        for i, (locale, stat) in enumerate(stats_to_download.iteritems()):
            catalog_for_meta = self.pod.catalogs.get(locale)
            thread = threading.Thread(
                target=self._update_meta, args=(stat, locale, catalog_for_meta))
            threads.append(thread)
            thread.start()
            if i == 0:
                thread.join()
            self.pod.logger.info('Meta information updated ({}): {}'.format(
                stat.lang, stat.url))
        for i, thread in enumerate(threads):
            if i > 0:
                thread.join()

    def upload(self, locales=None, force=True, verbose=False, save_stats=True,
               prune=False):
        source_lang = self.pod.podspec.default_locale
        locales = locales or self.pod.catalogs.list_locales()
        locales = self._cleanup_locales(locales)
        stats = []
        num_files = len(locales)
        if not locales:
            self.pod.logger.info('No locales to upload.')
            return
        if not force:
            if (self.has_immutable_translation_resources
                    and self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH)):
                text = 'Found existing translator data in: {}'
                self.pod.logger.info(text.format(
                    Translator.TRANSLATOR_STATS_PATH))
                text = 'This will be updated with new data after the upload is complete.'
                self.pod.logger.info(text)
            text = 'Proceed to upload {} translation catalogs?'
            text = text.format(num_files)
            if not utils.interactive_confirm(text):
                self.pod.logger.info('Aborted.')
                return
        if self.has_multiple_langs_in_one_resource:
            catalogs_to_upload = []
            for locale in locales:
                catalog_to_upload = self.pod.catalogs.get(locale)
                if catalog_to_upload:
                    catalogs_to_upload.append(catalog_to_upload)
            stats = self._upload_catalogs(catalogs_to_upload, source_lang,
                                          prune=prune)
        else:
            text = 'Uploading translations: %(value)d/{} (in %(time_elapsed).9s)'
            widgets = [progressbar.FormatLabel(text.format(num_files))]
            bar = progressbar_non.create_progressbar(
                "Uploading translations...", widgets=widgets, max_value=num_files)
            bar.start()
            threads = []

            def _do_upload(locale):
                catalog = self.pod.catalogs.get(locale)
                stat = self._upload_catalog(catalog, source_lang, prune=prune)
                stats.append(stat)
            for i, locale in enumerate(locales):
                thread = utils.ProgressBarThread(
                    bar, True, target=_do_upload, args=(locale,))
                threads.append(thread)
                thread.start()
                # Perform the first operation synchronously to avoid oauth2 refresh
                # locking issues.
                if i == 0:
                    thread.join()
            for i, thread in enumerate(threads):
                if i > 0:
                    thread.join()
            bar.finish()
        stats = sorted(stats, key=lambda stat: stat.lang)
        if verbose:
            self.pretty_print_stats(stats)
        if save_stats:
            self.save_stats(stats)
        return stats

    def save_stats(self, stats):
        """Merges a list of stats into the translator stats file."""
        if self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH):
            content = self.pod.read_yaml(Translator.TRANSLATOR_STATS_PATH)
            create = False
        else:
            content = {}
            create = True
        if self.KIND not in content:
            content[self.KIND] = {}
        for stat in copy.deepcopy(stats):
            content[self.KIND][stat.lang] = stat
        yaml_content = yaml.safe_dump(content, default_flow_style=False)
        self.pod.write_file(Translator.TRANSLATOR_STATS_PATH, yaml_content)
        if create:
            self.pod.logger.info('Saved: {}'.format(
                Translator.TRANSLATOR_STATS_PATH))
        else:
            self.pod.logger.info('Updated: {}'.format(
                Translator.TRANSLATOR_STATS_PATH))

    @classmethod
    def pretty_print_stats(cls, stats):
        table = texttable.Texttable(max_width=0)
        table.set_deco(texttable.Texttable.HEADER)
        rows = []
        rows.append(['Language', 'URL', 'Wordcount'])
        for stat in stats:
            rows.append([stat.lang, stat.url, stat.num_words or '--'])
        table.add_rows(rows)
        logging.info('\n' + table.draw() + '\n')

    def get_edit_url(self, doc):
        if not doc.locale:
            return
        stats = self._get_stats_to_download([doc.locale])
        if doc.locale not in stats:
            return
        stat = stats[doc.locale]
        return stat.url

    def inject(self, doc):
        if not self._inject or not doc.locale:
            return
        self.download(locales=[doc.locale], save_stats=False, inject=True)
        return self
