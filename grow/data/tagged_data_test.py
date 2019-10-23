"""Tests for tagged data."""

import unittest
from grow.data import tagged_data


class TaggedDataTestCase(unittest.TestCase):
    """Test the tagged data."""

    def test_hash(self):
        """Hash of the original data used for caching objects."""
        original = 'testing: true'
        data = tagged_data.TaggedData(original)
        self.assertEqual(data.hash, '7e00c7fe045a5725946bef34b57c934c7555a27d')

    def test_tagged(self):
        """Tagged and parsed source is not implemented."""
        original = 'testing: true'
        data = tagged_data.TaggedData(original)
        with self.assertRaises(NotImplementedError):
            _ = data.tagged

    def test_source(self):
        """Original source is available."""
        original = 'testing: true'
        data = tagged_data.TaggedData(original)
        self.assertEqual(data.source, original)
