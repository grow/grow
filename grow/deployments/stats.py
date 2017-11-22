"""Deployment stats tracking."""

import collections
import os
import texttable
from protorpc import protojson
from . import messages


class Stats(object):

    def __init__(self, pod, paths=None, full=True):
        self.full = full
        self.pod = pod
        self.paths = paths

    def get_num_files_per_type(self):
        file_counts = collections.defaultdict(int)
        if self.paths:
            for path in self.paths:
                ext = os.path.splitext(path)[-1]
                file_counts[ext] += 1
        ms = []
        for ext, count in file_counts.iteritems():
            ms.append(messages.FileCountMessage(ext=ext, count=count))
        return ms

    def to_message(self):
        message = messages.StatsMessage()
        collections = self.pod.list_collections()
        message.num_collections = len(collections)
        message.num_files_per_type = self.get_num_files_per_type()
        message.locales = [str(locale) for locale in self.pod.list_locales()]
        message.langs = self.pod.catalogs.list_locales()
        catalog = self.pod.catalogs.get_template()
        message.num_messages = len(catalog)
        return message

    def to_string(self):
        return protojson.encode_message(self.to_message())

    def to_tables(self):
        results = []

        table = texttable.Texttable(max_width=0)
        table.set_deco(texttable.Texttable.HEADER)
        rows = []
        rows.append(['Resource', 'Count'])

        all_collections = self.pod.list_collections()
        rows.append(['Collections', len(all_collections)])
        documents = []
        for collection in all_collections:
            documents += collection.list_docs()
        rows.append(['Documents', len(documents)])
        locales = self.pod.list_locales()
        rows.append(['Locales', len(locales)])
        if self.pod.use_reroute:
            self.pod.router.use_simple()
            self.pod.router.add_all()
            rows.append(['Routes', len(self.pod.router.routes)])
        else:
            routes = self.pod.routes
            rows.append(['Routes', len(routes.list_concrete_paths())])
        template = self.pod.catalogs.get_template()
        rows.append(['Messages', len(template)])
        table.add_rows(rows)
        content = table.draw()
        results.append(content)

        if self.full:
            table = texttable.Texttable(max_width=0)
            table.set_deco(texttable.Texttable.HEADER)
            rows = []
            rows.append(['File type', 'Count'])
            exts_and_counts = self.get_num_files_per_type()
            exts_and_counts = sorted(exts_and_counts,
                                     key=lambda message: -message.count)
            for message in exts_and_counts:
                ext = message.ext or '.html'
                rows.append([ext, message.count])
            table.add_rows(rows)
            content = table.draw()
            results.append(content)

        table = texttable.Texttable(max_width=0)
        table.set_deco(texttable.Texttable.HEADER)
        catalogs = sorted(self.pod.catalogs, key=str)
        rows = []
        rows.append(['Translations ({})'.format(len(catalogs)), 'Messages'])
        for catalog in catalogs:
            num_messages = len(catalog)
            untranslated_messages = catalog.list_untranslated()
            translated_messages = num_messages - len(untranslated_messages)
            label = '{} / {}'.format(translated_messages, num_messages)
            rows.append([str(catalog.locale), label])

        table.add_rows(rows)
        if catalogs:
            content = table.draw()
            results.append(content)

        return results
