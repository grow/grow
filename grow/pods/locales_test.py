from . import locales
import os
import unittest


class LocalesTest(unittest.TestCase):

  def test_eq(self):
    locale = locales.Locale('en_US')
    self.assertEqual(locale, 'en_US')
    self.assertEqual(locale, 'en_us')
    self.assertEqual(locale, locales.Locale('en_US'))


if __name__ == '__main__':
  unittest.main()
