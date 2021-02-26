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
    '†',
    '‡',
    '§',
    '||',
    '¶',
    '#',
]
NUMERICAL_SYMBOLS = {
    '0': '⁰',
    '1': '¹',
    '2': '²',
    '3': '³',
    '4': '⁴',
    '5': '⁵',
    '6': '⁶',
    '7': '⁷',
    '8': '⁸',
    '9': '⁹',
}
NUMERIC_LOCALES_REGEX = re.compile(r'_(DE)$', re.IGNORECASE)


class Error(Exception):

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class DuplicateSymbolError(Error, KeyError):
    pass


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


def numberic_generator():
    index = 1
    while True:
        yield index
        index += 1


class Footnotes(object):
    def __init__(self, locale, symbols=None, use_numeric=None,
            use_numeric_symbols=None, numeric_locales_pattern=None):
        self.symbol_to_footnote = collections.OrderedDict()
        self.symbols = symbols or SYMBOLS
        self.locale = locale
        self.use_numeric = use_numeric
        self.use_numeric_symbols = use_numeric_symbols
        if numeric_locales_pattern is not None:
            self.numeric_locales_pattern = re.compile(
                numeric_locales_pattern, re.IGNORECASE)
        else:
            self.numeric_locales_pattern = NUMERIC_LOCALES_REGEX
        self.reset()

    def __getitem__(self, key):
        return self.symbol_to_footnote[key]

    def __iter__(self):
        return self.symbol_to_footnote.items()

    def __len__(self):
        return len(self.symbol_to_footnote)

    @property
    def footnotes(self):
        return self.symbol_to_footnote

    @property
    def is_numeric(self):
        return (self.use_numeric
            or self.use_numeric_symbols
            or self.is_numeric_territory)

    @property
    def is_numeric_territory(self):
        if self.locale is None:
            return False
        # When explicitly not using numbers, do not use numeric.
        if self.use_numeric_symbols is False or self.use_numeric is False:
            return False
        return self.numeric_locales_pattern.search(self.locale) is not None

    def add(self, value, custom_symbol=None):
        for symbol, note_value in self.symbol_to_footnote.items():
            if value == note_value:
                return symbol

        if custom_symbol:
            # Check that the symbol is not in use.
            if custom_symbol in self.symbol_to_footnote.keys():
                raise DuplicateSymbolError(
                    'Custom symbol already in use: {}'.format(custom_symbol))
            self.symbol_to_footnote[custom_symbol] = value
            return custom_symbol

        # Doesn't exist, add as new symbol.
        symbol = next(self.generator)
        self.symbol_to_footnote[symbol] = value
        return symbol

    def index(self, key):
        return list(self.symbol_to_footnote.keys()).index(key)

    def items(self):
        return self.symbol_to_footnote.items()

    def reset(self):
        self.symbol_to_footnote = collections.OrderedDict()
        if self.is_numeric:
            if self.use_numeric:
                self.generator = numberic_generator()
            else:
                self.generator = numberic_symbol_generator()
        else:
            self.generator = symbol_generator(self.symbols)
