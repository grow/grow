"""Tests for grow.common.remap."""

import collections
import unittest

from grow.common import remap


class RemapTestCase(unittest.TestCase):

    def test_visit_and_drop(self):
        data = {
            'keep': 1,
            'drop': 2,
            'nested': [{'a': 10, 'drop': 20}],
        }
        result = remap.remap(
            data,
            visit=lambda _path, k, v: False if k == 'drop' else (k, v),
        )
        self.assertEqual({'keep': 1, 'nested': [{'a': 10}]}, result)

    def test_preserves_ordered_dict(self):
        data = collections.OrderedDict([('b', 2), ('a', 1)])
        result = remap.remap(data)
        self.assertIsInstance(result, collections.OrderedDict)
        self.assertEqual([('b', 2), ('a', 1)], list(result.items()))
