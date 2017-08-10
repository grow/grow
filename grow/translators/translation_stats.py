"""Translation stats collection and reporting."""

import logging
import texttable


class TranslationStats(object):

    ROW_COUNT = 7

    def __init__(self):
        self._locale_to_message = {}
        self._untranslated = {}

    @property
    def messages(self):
        return self._locale_to_message

    @property
    def untranslated(self):
        tracking = {}
        for locale, messages in self._untranslated.iteritems():
            if locale not in tracking:
                tracking[locale] = {}
            for message in messages:
                tracking[locale][message] = self._locale_to_message[
                    locale][message]
        return tracking

    def export(self):
        return {
            'messages': self.messages,
            'untranslated': self.untranslated,
        }

    def export_untranslated_catalogs(self, pod, dir_path=None):
        """Export the untranslated messages into catalogs based on locale."""
        locale_to_catalog = {}
        for locale, messages in self.untranslated.iteritems():
            if locale not in locale_to_catalog:
                locale_to_catalog[locale] = pod.catalogs.get(
                    locale, basename='untranslated.po', dir_path=dir_path)
            catalog = locale_to_catalog[locale]
            for message in messages:
                catalog.add(message)
        return locale_to_catalog

    def tick(self, message, locale, default_locale):
        if not message:
            return

        if locale not in self._locale_to_message:
            self._locale_to_message[locale] = {}

        messages = self._locale_to_message[locale]
        if message.id not in messages:
            messages[message.id] = 0
        messages[message.id] += 1

        if not message.string and locale is not default_locale:
            if locale not in self._untranslated:
                self._untranslated[locale] = set()
            self._untranslated[locale].add(message.id)

    def pretty_print(self, show_all=False):
        """Outputs the translation stats to a table formatted view."""

        # Most frequent untranslated messages.
        table = texttable.Texttable(max_width=120)
        table.set_deco(texttable.Texttable.HEADER)
        table.set_cols_dtype(['t', 'i', 't'])
        table.set_cols_align(['l', 'r', 'l'])
        rows = []

        for locale in self.untranslated:
            for message in self.untranslated[locale]:
                rows.append([str(locale), self.untranslated[
                            locale][message], message])

        rows = sorted(rows, key=lambda x: -x[1])
        if not show_all:
            num_rows = len(rows)
            rows = rows[:self.ROW_COUNT]
            if num_rows > self.ROW_COUNT:
                rows.append(['', num_rows - self.ROW_COUNT,
                             '+ Additional untranslated strings...'])

        table.add_rows([['Locale', '#', 'Untranslated Message']] + rows)
        logging.info('\n' + table.draw() + '\n')

        # Untranslated messages per locale.
        table = texttable.Texttable(max_width=120)
        table.set_deco(texttable.Texttable.HEADER)
        table.set_cols_dtype(['t', 'i'])
        table.set_cols_align(['l', 'r'])
        rows = []

        for locale in self.untranslated:
            rows.append([str(locale), len(self.untranslated[locale])])

        rows = sorted(rows, key=lambda x: -x[1])

        table.add_rows([['Locale', 'Untranslated']] + rows)
        logging.info('\n' + table.draw() + '\n')
