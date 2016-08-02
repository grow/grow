from grow.testing import testing
from grow.common.sdk_utils import get_this_version, LatestVersionCheckError
from . import utils
import copy
import mock
import semantic_version
import unittest


class UtilsTestCase(unittest.TestCase):

    def test_walk(self):
        data = {
          'foo': 'bar',
          'bam': {
            'foo': 'bar2',
            'foo2': ['bar3', 'bar4'],
          }
        }

        actual = []
        callback = lambda item, key, node: actual.append(item)
        utils.walk(data, callback)

        expected = ['bar', 'bar2', 'bar3', 'bar4']
        self.assertItemsEqual(expected, actual)

    def test_parse_yaml(self):
        pod = testing.create_test_pod()
        content = pod.read_file('/data/constructors.yaml')
        result = utils.parse_yaml(content, pod=pod)
        doc = pod.get_doc('/content/pages/home.yaml')
        self.assertEqual(doc, result['doc'])
        expected_docs = [
            pod.get_doc('/content/pages/home.yaml'),
            pod.get_doc('/content/pages/about.yaml'),
            pod.get_doc('/content/pages/home.yaml'),
        ]
        self.assertEqual(expected_docs, result['docs'])

    def test_version_enforcement(self):
        with mock.patch('grow.pods.pods.Pod.grow_version',
                        new_callable=mock.PropertyMock) as mock_version:
            this_version = get_this_version()
            gt_version = '>{0}'.format(semantic_version.Version(this_version))
            mock_version.return_value = gt_version
            with self.assertRaises(LatestVersionCheckError):
                pod = testing.create_test_pod()

    def test_untag_fields(self):
        fields_to_test = {
            'title': 'value-none',
            'title@fr': 'value-fr',
            'list': [
                {
                    'list-item-title': 'value-none',
                    'list-item-title@fr': 'value-fr',
                },
            ],
            'sub-nested': {
                'sub-nested': {
                    'nested@': 'sub-sub-nested-value',
                },
            },
            'nested': {
                'nested-none': 'nested-value-none',
                'nested-title@': 'nested-value-none',
            },
            'nested@fr': {
                'nested-title@': 'nested-value-fr',
            },
            'list@de': [
                'list-item-de',
            ]
        }
        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'value-fr',
            'list': [{'list-item-title': 'value-fr'},],
            'nested': {'nested-title': 'nested-value-fr',},
            'sub-nested': {
                'sub-nested': {
                    'nested': 'sub-sub-nested-value',
                },
            },
        }, utils.untag_fields(fields, locale='fr'))

        fields = copy.deepcopy(fields_to_test)
        self.assertDictEqual({
            'title': 'value-none',
            'list': ['list-item-de',],
            'nested': {
                'nested-none': 'nested-value-none',
                'nested-title': 'nested-value-none',
            },
            'sub-nested': {
                'sub-nested': {
                    'nested': 'sub-sub-nested-value',
                },
            },
        }, utils.untag_fields(fields, locale='de'))


if __name__ == '__main__':
    unittest.main()
