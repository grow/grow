"""Tests for the common utility methods."""

import unittest

import yaml

from grow.common import utils, yaml_utils
from grow.testing import testing


class YamlUtilsTestCase(unittest.TestCase):
    """Test specialized yaml utilities."""

    def test_plaintext_yaml(self):
        """Plaintext parsing of yaml without the constructors."""
        pod = testing.create_test_pod()
        content = pod.read_file('/data/constructors.yaml')
        result = yaml.load(content, Loader=yaml_utils.PlainTextYamlLoader)
        self.assertEqual(result['doc'], {'tag': '!g.doc', 'value': '/content/pages/home.yaml'})
        self.assertEqual(
            result['unfathomable'], {'tag': '!g.yaml', 'value': '/data/deep.yaml?not.really.there'}
        )

    def test_unsafe_yaml_tags_rejected(self):
        """Safe YAML loaders must reject arbitrary Python object tags."""
        malicious = '!!python/object/apply:os.system ["echo pwned"]'
        with self.assertRaises(yaml.constructor.ConstructorError):
            yaml.load(malicious, Loader=yaml_utils.PlainTextYamlLoader)
        with self.assertRaises(yaml.constructor.ConstructorError):
            utils.parse_yaml(malicious)


if __name__ == '__main__':
    unittest.main()
