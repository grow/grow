# -*- coding: utf-8 -*-
"""Tests for footnotes."""

import unittest
from grow.pods import footnotes


class SymbolGeneratorTestCase(unittest.TestCase):

    def test_symbol_generator(self):
        generator = footnotes.symbol_generator()

        expected = [
            '*', u'†', u'‡', u'§', u'||', u'¶', '#',
            '**', u'††', u'‡‡', u'§§', u'||||', u'¶¶', '##',
            '***', u'†††', u'‡‡‡', u'§§§', u'||||||', u'¶¶¶', '###',
        ]
        actual = []
        for _ in range(21):
            actual.append(next(generator))
        self.assertEquals(expected, actual)

    def test_symbol_generator_symbols(self):
        symbols = ['*', u'†', u'‡', u'§',]
        generator = footnotes.symbol_generator(symbols=symbols)

        expected = [
            '*', u'†', u'‡', u'§', '**', u'††', u'‡‡', u'§§', '***', u'†††',
        ]
        actual = []
        for _ in range(10):
            actual.append(next(generator))
        self.assertEquals(expected, actual)

class NumberSymbolGeneratorTestCase(unittest.TestCase):

    def test_numberic_symbol_generator(self):
        generator = footnotes.numberic_symbol_generator()

        expected = [
            u'¹', u'²', u'³', u'⁴', u'⁵', u'⁶', u'⁷', u'⁸', u'⁹', u'¹⁰',
            u'¹¹', u'¹²', u'¹³', u'¹⁴', u'¹⁵', u'¹⁶', u'¹⁷', u'¹⁸', u'¹⁹',
            u'²⁰', u'²¹',
        ]
        actual = []
        for _ in range(21):
            actual.append(next(generator))
        self.assertEquals(expected, actual)


class FootnotesTestCase(unittest.TestCase):

    def test_add(self):
        notes = footnotes.Footnotes(None)
        symbol = notes.add('See other side.')
        self.assertEquals(1, len(notes))
        self.assertEquals('*', symbol)
        self.assertEquals('See other side.', notes[symbol])
        self.assertDictEqual({'*': 'See other side.'}, notes.footnotes)

    def test_add_duplicate(self):
        # Adding duplicate footnotes does not create new footnotes.
        notes = footnotes.Footnotes(None)
        symbol = notes.add('See other side.')
        self.assertEquals(1, len(notes))
        self.assertEquals('*', symbol)
        symbol = notes.add('See other side.')
        self.assertEquals(1, len(notes))
        self.assertEquals('*', symbol)

    def test_index(self):
        notes = footnotes.Footnotes(None)
        symbol = notes.add('See other side.')
        self.assertEquals(0, notes.index(symbol))
        symbol = notes.add('Nothing to see here.')
        self.assertEquals(1, notes.index(symbol))

    def test_locale_pattern(self):
        notes = footnotes.Footnotes(None)
        self.assertEquals(False, notes.is_numeric)

        notes = footnotes.Footnotes('de_DE')
        self.assertEquals(True, notes.is_numeric)

        notes = footnotes.Footnotes('en_US')
        self.assertEquals(False, notes.is_numeric)

    def test_locale_pattern_custom(self):
        notes = footnotes.Footnotes(
            'en_US', numeric_locales_pattern='_US$')
        self.assertEquals(True, notes.is_numeric)

    def test_use_numeric_symbols(self):
        # Defaults to pattern for detection.
        notes = footnotes.Footnotes('de_DE')
        self.assertEquals(True, notes.is_numeric)

        notes = footnotes.Footnotes('en_US')
        self.assertEquals(False, notes.is_numeric)

        # Ignores the pattern when false.
        notes = footnotes.Footnotes(
            'de_DE', use_numeric_symbols=False)
        self.assertEquals(False, notes.is_numeric)

        notes = footnotes.Footnotes(
            'en_US', use_numeric_symbols=False)
        self.assertEquals(False, notes.is_numeric)

        # Ignores the pattern when true.
        notes = footnotes.Footnotes(
            'de_DE', use_numeric_symbols=True)
        self.assertEquals(True, notes.is_numeric)

        notes = footnotes.Footnotes(
            'en_US', use_numeric_symbols=True)
        self.assertEquals(True, notes.is_numeric)


if __name__ == '__main__':
    unittest.main()
