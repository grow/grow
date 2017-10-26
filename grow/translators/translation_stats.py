"""Translation stats collection and reporting."""

import datetime
import io
import logging
import traceback
import texttable


class TranslationStats(object):

    ROW_COUNT = 7

    def __init__(self):
        self._locale_to_message = {}
        self._untranslated = {}
        self._stacktraces = []

    @property
    def messages(self):
        """All messages and counts."""
        return self._locale_to_message

    @property
    def untranslated(self):
        """Untranslated messages by locale."""
        tracking = {}
        for locale, messages in self._untranslated.iteritems():
            if locale not in tracking:
                tracking[locale] = {}
            for message in messages:
                tracking[locale][message] = self._locale_to_message[
                    locale][message]
        return tracking

    @property
    def count_untranslated(self):
        """Max number of untranslated strings for any locale."""
        untranslated_ids = set()
        for _, messages in self._untranslated.iteritems():
            for message in messages:
                untranslated_ids.add(message)
        return len(untranslated_ids)

    @property
    def stacktraces(self):
        return self._stacktraces

    @staticmethod
    def _simplify_traceback(tb):
        """Remove extra layers of the traceback to just get best bits."""
        start = 0
        end = len(tb) - 3
        for i, item in enumerate(tb):
            if 'jinja' in item:
                start = i + 1
                break
        return tb[start:end]

    def _get_message_locations(self, locale, message):
        """Get a list of the locations for a given locale and message."""
        locations = set()

        for item in self.stacktraces:
            if item['locale'] != locale or item['id'] != message:
                continue
            if item['location']:
                locations.add(item['location'])

        return [(location, None) for location in locations]

    def export(self):
        """Export messages and untranslated strings."""
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
                catalog.add(message, locations=self._get_message_locations(
                    locale, message))
        return locale_to_catalog

    def export_untranslated_tracebacks(self):
        """Export the untranslated tracebacks into a log file."""
        width = 70
        border_width = 3
        border_char = '='

        def _blank_line():
            return u'\n'

        def _solid_line():
            return u'{}\n'.format(border_char * width)

        def _text_line(text):
            text_width = width - (border_width + 1) * 2
            return u'{} {} {}\n'.format(
                border_char * border_width, text.center(text_width),
                border_char * border_width)

        with io.StringIO() as output:
            output.write(_solid_line())
            output.write(_text_line(u'Untranslated Strings'))
            output.write(_solid_line())
            output.write(_text_line(
                u'{} occurrences of {} untranslated strings'.format(
                    len(self.stacktraces), self.count_untranslated)))
            output.write(_text_line(str(datetime.datetime.now())))
            output.write(_solid_line())
            output.write(_blank_line())

            if not self.stacktraces:
                output.write(
                    _text_line(u'No untranslated strings found.'))
                return output.getvalue().encode('utf-8')

            for item in self.stacktraces:
                output.write(u'{} :: {}\n'.format(item['locale'], item['id']))
                for line in item['tb']:
                    output.write(u'{}'.format(line))
                output.write(_blank_line())

            return output.getvalue().encode('utf-8')

    def tick(self, message, locale, default_locale, location=None):
        """Count a translation."""
        if not message:
            return

        if locale not in self._locale_to_message:
            self._locale_to_message[locale] = {}

        messages = self._locale_to_message[locale]
        if message.id not in messages:
            messages[message.id] = 0
        messages[message.id] += 1

        # Check for untranslated message.
        if not message.string and message.id.strip() and locale is not default_locale:
            if locale not in self._untranslated:
                self._untranslated[locale] = set()

            stack = traceback.format_stack()
            self._stacktraces.append({
                'locale': locale,
                'location': location,
                'id': message.id,
                'tb': self._simplify_traceback(stack),
            })
            self._untranslated[locale].add(message.id)

    def pretty_print(self, show_all=False):
        """Outputs the translation stats to a table formatted view."""

        if not self.untranslated:
            logging.info('\nNo untranslated strings found.\n')
            return

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
