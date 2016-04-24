from protorpc import message_types
from protorpc import messages
from protorpc import protojson
import copy
import json
import logging
import texttable
import yaml


class TranslatorStat(messages.Message):
    lang = messages.StringField(1)
    num_words = messages.IntegerField(2)
    num_words_translated = messages.IntegerField(3)
    source_lang = messages.StringField(4)
    ident = messages.StringField(5)
    edit_url = messages.StringField(6)
    created = message_types.DateTimeField(7)


class Translator(object):
    TRANSLATOR_STATS_PATH = '/translations/translators.yaml'

    def __init__(self, pod, config=None):
        self.pod = pod
        self.config = config or {}

    def download(self, locales):
        if not self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH):
            text = 'File {} not found. Nothing to download.'
            self.pod.logger.info(text.format(Translator.TRANSLATOR_STATS_PATH))
            return
        stats = self.pod.read_yaml(Translator.TRANSLATOR_STATS_PATH)
        for lang, stat in stats['translators'].iteritems():
            stat['lang'] = lang
            stat = json.dumps(stat)
            stat = protojson.decode_message(TranslatorStat, stat)
            content = self._download_content(stat)
            self.pod.catalogs.import_translations(locale=lang, content=content)

    def upload(self, locales, force=True, save=True):
        # TODO: Upload progress and prompt.
        source_lang = self.pod.podspec.default_locale
        locales = locales or self.pod.catalogs.list_locales()
        stats = []
        for locale in locales:
            catalog = self.pod.catalogs.get(locale)
            stat = self._upload_catalog(catalog, source_lang)
            stats.append(stat)
        if save:
            self.save_stats(stats)
        stat = sorted(stats, key=lambda stat: stat.lang)
        return stats

    def save_stats(self, stats):
        if self.pod.file_exists(Translator.TRANSLATOR_STATS_PATH):
            content = self.pod.read_yaml(Translator.TRANSLATOR_STATS_PATH)
        else:
            content = {'translators': {}}
        for stat in copy.deepcopy(stats):
            stat_json = json.loads(protojson.encode_message(stat))
            lang = stat_json.pop('lang')
            content['translators'][lang] = stat_json
        yaml_content = yaml.safe_dump(content, default_flow_style=False)
        self.pod.write_file(Translator.TRANSLATOR_STATS_PATH, yaml_content)
        self.pod.logger.info('Saved: {}'.format(Translator.TRANSLATOR_STATS_PATH))

    @classmethod
    def pretty_print_stats(cls, stats):
        table = texttable.Texttable(max_width=0)
        table.set_deco(texttable.Texttable.HEADER)
        rows = []
        rows.append(['Language', 'Edit URL', 'Wordcount'])
        for stat in stats:
            rows.append([stat.lang, stat.edit_url, stat.num_words])
        table.add_rows(rows)
        logging.info('\n' + table.draw() + '\n')
