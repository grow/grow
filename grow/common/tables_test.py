"""Tests for grow.common.tables."""

import unittest

from grow.common import tables


class TablesTestCase(unittest.TestCase):
    def test_header_table_and_alignment(self):
        table = tables.Texttable(max_width=0)
        table.set_deco(tables.Texttable.HEADER)
        table.set_cols_dtype(['t', 'i'])
        table.set_cols_align(['l', 'r'])
        table.add_rows([['Locale', 'Count'], ['en', 42], ['de', 7]])
        output = table.draw()
        lines = output.splitlines()
        self.assertEqual(4, len(lines))
        self.assertIn('Locale', lines[0])
        self.assertTrue(set(lines[1]) == {'='})
        self.assertTrue(lines[2].endswith('42'))
        self.assertTrue(lines[3].endswith(' 7'))

    def test_color_string(self):
        colored = tables.get_color_string(tables.bcolors.GREEN, 'add')
        self.assertEqual('\033[92madd\033[0m', colored)
