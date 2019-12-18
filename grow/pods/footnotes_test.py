# -*- coding: utf-8 -*-
"""Tests for footnotes."""

import unittest
from grow.pods import footnotes


class SymbolGeneratorTestCase(unittest.TestCase):

    def test_symbol_generator(self):
        generator = footnotes.symbol_generator()

        expected = [
            '*', '†', '‡', '§', '||', '¶', '#',
            '**', '††', '‡‡', '§§', '||||', '¶¶', '##',
            '***', '†††', '‡‡‡', '§§§', '||||||', '¶¶¶', '###',
        ]
        actual = []
        for _ in range(21):
            actual.append(next(generator))
        self.assertEqual(expected, actual)

    def test_symbol_generator_symbols(self):
        symbols = ['*', '†', '‡', '§',]
        generator = footnotes.symbol_generator(symbols=symbols)

        expected = [
            '*', '†', '‡', '§', '**', '††', '‡‡', '§§', '***', '†††',
        ]
        actual = []
        for _ in range(10):
            actual.append(next(generator))
        self.assertEqual(expected, actual)

class NumberSymbolGeneratorTestCase(unittest.TestCase):

    def test_numberic_symbol_generator(self):
        generator = footnotes.numberic_symbol_generator()

        expected = [
            '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', '¹⁰',
            '¹¹', '¹²', '¹³', '¹⁴', '¹⁵', '¹⁶', '¹⁷', '¹⁸', '¹⁹',
            '²⁰', '²¹',
        ]
        actual = []
        for _ in range(21):
            actual.append(next(generator))
        self.assertEqual(expected, actual)


class FootnotesTestCase(unittest.TestCase):

    def test_add(self):
        notes = footnotes.Footnotes(None)
        symbol = notes.add('See other side.')
        self.assertEqual(1, len(notes))
        self.assertEqual('*', symbol)
        self.assertEqual('See other side.', notes[symbol])
        self.assertDictEqual({'*': 'See other side.'}, notes.footnotes)

    def test_add_duplicate(self):
        # Adding duplicate footnotes does not create new footnotes.
        notes = footnotes.Footnotes(None)
        symbol = notes.add('See other side.')
        self.assertEqual(1, len(notes))
        self.assertEqual('*', symbol)
        symbol = notes.add('See other side.')
        self.assertEqual(1, len(notes))
        self.assertEqual('*', symbol)

    def test_index(self):
        notes = footnotes.Footnotes(None)
        symbol = notes.add('See other side.')
        self.assertEqual(0, notes.index(symbol))
        symbol = notes.add('Nothing to see here.')
        self.assertEqual(1, notes.index(symbol))

    def test_locale_pattern(self):
        notes = footnotes.Footnotes(None)
        self.assertEqual(False, notes.is_numeric)

        notes = footnotes.Footnotes('de_DE')
        self.assertEqual(True, notes.is_numeric)

        notes = footnotes.Footnotes('en_US')
        self.assertEqual(False, notes.is_numeric)

    def test_locale_pattern_custom(self):
        notes = footnotes.Footnotes(
            'en_US', numeric_locales_pattern='_US$')
        self.assertEqual(True, notes.is_numeric)

    def test_reset(self):
        """Resetting resets the footnotes and the symbol generator."""
        notes = footnotes.Footnotes(None)
        symbol = notes.add('See other side.')
        self.assertEqual(1, len(notes))
        self.assertEqual('*', symbol)
        self.assertEqual('See other side.', notes[symbol])

        notes.reset()

        self.assertEqual(0, len(notes))
        symbol = notes.add('See this side.')
        self.assertEqual(1, len(notes))
        self.assertEqual('*', symbol)
        self.assertEqual('See this side.', notes[symbol])

    def test_use_numeric_symbols(self):
        # Defaults to pattern for detection.
        notes = footnotes.Footnotes('de_DE')
        self.assertEqual(True, notes.is_numeric)

        notes = footnotes.Footnotes('en_US')
        self.assertEqual(False, notes.is_numeric)

        # Ignores the pattern when false.
        notes = footnotes.Footnotes(
            'de_DE', use_numeric_symbols=False)
        self.assertEqual(False, notes.is_numeric)

        notes = footnotes.Footnotes(
            'en_US', use_numeric_symbols=False)
        self.assertEqual(False, notes.is_numeric)

        # Ignores the pattern when true.
        notes = footnotes.Footnotes(
            'de_DE', use_numeric_symbols=True)
        self.assertEqual(True, notes.is_numeric)

        notes = footnotes.Footnotes(
            'en_US', use_numeric_symbols=True)
        self.assertEqual(True, notes.is_numeric)


if __name__ == '__main__':
    unittest.main()
