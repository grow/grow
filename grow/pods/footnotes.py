# -*- coding: utf-8 -*-
"""Footnotes for documents using chicago manual style.

By default specific languages forgo the symbol based footnotes.

https://en.wikipedia.org/wiki/Dagger_(typography) :
While daggers are freely used in English-language texts, they are often avoided
in other languages because of their similarity to the Christian cross. In
German, for example, daggers are commonly employed only to indicate a person's
death or the extinction of a word, language, species or the like.

http://graphicdesign.stackexchange.com/questions/10892/footnote-typographic-conventions :
In Germany the two footnote signs * † have also the meaning of born (*) and died (†)
"""

import collections
import re

SYMBOLS = [
    '*',
    u'†',
    u'‡',
    u'§',
    u'||',
    u'¶',
    '#',
]
NUMERICAL_SYMBOLS = {
    u'0': u'⁰',
    u'1': u'¹',
    u'2': u'²',
    u'3': u'³',
    u'4': u'⁴',
    u'5': u'⁵',
    u'6': u'⁶',
    u'7': u'⁷',
    u'8': u'⁸',
    u'9': u'⁹',
}
NUMERIC_LOCALES_REGEX = re.compile(r'_(DE)$', re.IGNORECASE)


def symbol_generator(symbols=SYMBOLS):
    loop_count = 1
    loop_index = 0
    while True:
        if loop_index > len(symbols) - 1:
            loop_count += 1
            loop_index = 0
        yield symbols[loop_index] * loop_count
        loop_index += 1


def numberic_symbol_generator():
    index = 1
    while True:
        yield ''.join([NUMERICAL_SYMBOLS[char] for char in str(index)])
        index += 1


class Footnotes(object):

    def __init__(self, locale, symbols=None, use_numeric_symbols=None,
            numeric_locales_pattern=None):
        self.symbol_to_footnote = collections.OrderedDict()
        symbols = symbols or SYMBOLS
        numeric_locales_pattern = (
            numeric_locales_pattern or NUMERIC_LOCALES_REGEX)
        if type(NUMERIC_LOCALES_REGEX) != type(numeric_locales_pattern):
            numeric_locales_pattern = re.compile(
                numeric_locales_pattern, re.IGNORECASE)
        is_numeric_territory = (locale is not None
            and numeric_locales_pattern.search(locale))
        if use_numeric_symbols != False and (
                use_numeric_symbols == True or is_numeric_territory):
            self.generator = numberic_symbol_generator()
            self.is_numeric = True
        else:
            self.generator = symbol_generator(symbols)
            self.is_numeric = False

    def __getitem__(self, key):
        return self.symbol_to_footnote[key]

    def __iter__(self):
        return self.symbol_to_footnote.iteritems()

    def __len__(self):
        return len(self.symbol_to_footnote)

    @property
    def footnotes(self):
        return self.symbol_to_footnote

    def add(self, value):
        for symbol, note_value in self.symbol_to_footnote.iteritems():
            if value == note_value:
                return symbol

        # Doesn't exist, add as new symbol.
        symbol = next(self.generator)
        self.symbol_to_footnote[symbol] = value
        return symbol

    def index(self, key):
        return self.symbol_to_footnote.keys().index(key)

    def items(self):
        return self.symbol_to_footnote.items()

    def iteritems(self):
        return self.symbol_to_footnote.iteritems()
