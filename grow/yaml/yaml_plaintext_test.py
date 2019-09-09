"""Tests for the plaintext yaml loader."""

import textwrap
import unittest
from grow.yaml import yaml_plaintext


class YamlPlaintextTestCase(unittest.TestCase):
    """Test plaintext yaml utilities."""

    def test_plaintext_yaml(self):
        """Plaintext parsing of yaml without the constructors."""
        raw_yaml = textwrap.dedent("""
            doc: !g.doc /content/pages/home.yaml
            unfathomable: !g.yaml /data/deep.yaml?not.really.there
            """)
        result = yaml_plaintext.load_yaml(raw_yaml)
        self.assertEqual(
            result['doc'], {'tag': u'!g.doc', 'value': u'/content/pages/home.yaml'})
        self.assertEqual(result['unfathomable'], {
            'tag': u'!g.yaml',
            'value': u'/data/deep.yaml?not.really.there'
        })
