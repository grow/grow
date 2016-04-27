from protorpc import message_types
from protorpc import messages
from protorpc import protojson
from grow.common import utils
import copy
import json
import logging
import progressbar
import texttable
import threading
import yaml


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


class TranslatorServiceError(Exception):

    def __init__(self, message, ident=None, locale=None):
        if locale:
            new_message = 'Error for locale "{}" -> {}'.format(locale, message)
        elif ident:
            new_message = 'Error for resource "{}" -> {}'.format(ident, message)
        else:
            new_message = message
        super(TranslatorServiceError, self).__init__(new_message)


class Translator(object):
    TRANSLATOR_STATS_PATH = '/translations/translators.yaml'
    KIND = None
    has_immutable_translation_resources = False

    def __init__(self, pod, config=None, project_title=None,
                 instructions=None):
        self.pod = pod
        self.config = config or {}
        self.project_title = project_title or 'Untitled Grow Website'
        self.instructions = instructions

    def _download_content(self, stat):
        raise NotImplementedError

    def _upload_catalog(self, catalog, source_lang):
        raise NotImplementedError

    def _update_acl(self, stat, locale):
        raise NotImplementedError

    def _get_stats_to_download(self, locales):
        # 'stats' maps the service name to a mapping of languages to stats.
        stats = self.pod.read_yaml(Translator.TRANSLATOR_STATS_PATH)
        if self.KIND not in stats:
            self.pod.logger.info('Nothing found to download from {}'.format(self.KIND))
            return
        stats_to_download = stats[self.KIND]
        if locales:
            stats_to_download = dict([(lang, stat)
                                      for (lang, stat) in stats_to_download.iteritems()
                                      if lang in locales])
        for lang, stat in stats_to_download.iteritems():
            stat['lang'] = lang
            stat = json.dumps(stat)
            stat_message = protojson.decode_message(TranslatorStat, stat)
            stats_to_download[lang] = stat_message
        return stats_to_download

    def download(self, locales, save_stats=True):
        if not self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH):
            text = 'File {} not found. Nothing to download.'
            self.pod.logger.info(text.format(Translator.TRANSLATOR_STATS_PATH))
            return
        stats_to_download = self._get_stats_to_download(locales)
        if not stats_to_download:
            return
        num_files = len(stats_to_download)
        text = 'Downloading translations: %(value)d/{} (in %(elapsed)s)'
        widgets = [progressbar.FormatLabel(text.format(num_files))]
        bar = progressbar.ProgressBar(widgets=widgets, maxval=num_files)
        bar.start()
        threads = []
        langs_to_translations = {}
        new_stats = []
        def _do_download(lang, stat):
            new_stat, content = self._download_content(stat)
            new_stat.uploaded = stat.uploaded  # Preserve uploaded field.
            langs_to_translations[lang] = content
            new_stats.append(new_stat)
        for i, (lang, stat) in enumerate(stats_to_download.iteritems()):
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
        for lang, translations in langs_to_translations.iteritems():
            self.pod.catalogs.import_translations(locale=lang, content=translations)
        if save_stats:
            self.save_stats(new_stats)
        return new_stats

    def update_acl(self, locales=None):
        locales = locales or self.pod.catalogs.list_locales()
        if not locales:
            self.pod.logger.info('No locales to found to update.')
            return
        stats_to_download = self._get_stats_to_download(locales)
        if not stats_to_download:
            self.pod.logger.info('No documents found to update.')
            return
        threads = []
        for i, (locale, stat) in enumerate(stats_to_download.iteritems()):
            thread = threading.Thread(target=self._update_acl, args=(stat, locale))
            threads.append(thread)
            thread.start()
            if i == 0:
                thread.join()
            self.pod.logger.info('ACL updated ({}): {}'.format(stat.lang, stat.url))
        for i, thread in enumerate(threads):
            if i > 0:
                thread.join()

    def upload(self, locales=None, force=True, verbose=False, save_stats=True):
        source_lang = self.pod.podspec.default_locale
        locales = locales or self.pod.catalogs.list_locales()
        stats = []
        num_files = len(locales)
        if not locales:
            self.pod.logger.info('No locales to upload.')
            return
        if not force:
            if (self.has_immutable_translation_resources
                    and self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH)):
                text = 'Found existing translator data in: {}'
                self.pod.logger.info(text.format(Translator.TRANSLATOR_STATS_PATH))
                text = 'This will be updated with new data after the upload is complete.'
                self.pod.logger.info(text)
            text = 'Proceed to upload {} translation catalogs?'
            text = text.format(num_files)
            if not utils.interactive_confirm(text):
                self.pod.logger.info('Aborted.')
                return
        text = 'Uploading translations: %(value)d/{} (in %(elapsed)s)'
        widgets = [progressbar.FormatLabel(text.format(num_files))]
        bar = progressbar.ProgressBar(widgets=widgets, maxval=num_files)
        bar.start()
        threads = []
        def _do_upload(locale):
            catalog = self.pod.catalogs.get(locale)
            stat = self._upload_catalog(catalog, source_lang)
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
            stat_json = json.loads(protojson.encode_message(stat))
            lang = stat_json.pop('lang')
            content[self.KIND][lang] = stat_json
        yaml_content = yaml.safe_dump(content, default_flow_style=False)
        self.pod.write_file(Translator.TRANSLATOR_STATS_PATH, yaml_content)
        if create:
            self.pod.logger.info('Saved: {}'.format(Translator.TRANSLATOR_STATS_PATH))
        else:
            self.pod.logger.info('Updated: {}'.format(Translator.TRANSLATOR_STATS_PATH))

    @classmethod
    def pretty_print_stats(cls, stats):
        table = texttable.Texttable(max_width=0)
        table.set_deco(texttable.Texttable.HEADER)
        rows = []
        rows.append(['Language', 'URL', 'Wordcount'])
        for stat in stats:
            rows.append([stat.lang, stat.url, stat.num_words])
        table.add_rows(rows)
        logging.info('\n' + table.draw() + '\n')
