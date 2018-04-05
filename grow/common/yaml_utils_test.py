"""Tests for the common utility methods."""

import unittest
import yaml
from grow.testing import testing
from grow.common import yaml_utils


class YamlUtilsTestCase(unittest.TestCase):
    """Test specialized yaml utilities."""

    def test_plaintext_yaml(self):
        """Plaintext parsing of yaml without the constructors."""
        pod = testing.create_test_pod()
        content = pod.read_file('/data/constructors.yaml')
        result = yaml.load(content, Loader=yaml_utils.PlainTextYamlLoader)
        self.assertEqual(
            result['doc'], {'tag': u'!g.doc', 'value': u'/content/pages/home.yaml'})
        self.assertEqual(result['unfathomable'], {
            'tag': u'!g.yaml',
            'value': u'/data/deep.yaml?not.really.there'
        })


if __name__ == '__main__':
    unittest.main()
