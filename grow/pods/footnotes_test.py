# -*- coding: utf-8 -*-

from grow.pods import footnotes
from grow.pods import locales
import unittest


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
        self.assertEquals('See other side.', notes['*'])
        self.assertDictEqual({'*': 'See other side.'}, notes.footnotes)

    def test_locale_territories(self):
        notes = footnotes.Footnotes(None)
        self.assertEquals(False, notes.is_numeric)

        locale = locales.Locale.parse('en_CA')
        notes = footnotes.Footnotes(locale)
        self.assertEquals(True, notes.is_numeric)

        locale = locales.Locale.parse('de_DE')
        notes = footnotes.Footnotes(locale)
        self.assertEquals(True, notes.is_numeric)

        locale = locales.Locale.parse('en_US')
        notes = footnotes.Footnotes(locale)
        self.assertEquals(False, notes.is_numeric)


if __name__ == '__main__':
    unittest.main()
