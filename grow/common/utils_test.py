# coding: utf8
"""Tests for the common utility methods."""

import unittest
import mock
import semantic_version
from grow.testing import testing
from grow.common import config
from grow.sdk import updater
from grow.pods import errors
from . import utils


class UtilsTestCase(unittest.TestCase):

    def test_clean_google_href(self):
        # Test without a match.
        raw_input = '<a href="https://grow.io/">Link</a>'
        expected = '<a href="https://grow.io/">Link</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

        # Test with ?q=
        raw_input = '<a href="https://www.google.com/url?q=https%3A%2F%2Fgrow.io%2Fdocs%2F">Google Search</a>'
        expected = '<a href="https://grow.io/docs/">Google Search</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

        # Test with &q=
        raw_input = '<a href="https://www.google.com/url?sa=t&q=https%3A%2F%2Fgrow.io%2Fdocs%2F">Google Search</a>'
        expected = '<a href="https://grow.io/docs/">Google Search</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

    def test_clean_html_markdown(self):
        # Test without a match.
        raw_input = '<a href="https://grow.io/">Link</a>'
        expected = '[Link](https://grow.io/)'
        actual = utils.clean_html(raw_input, convert_to_markdown=True)
        self.assertEqual(expected, actual)

    def test_every_two(self):
        raw_input = [1, 2, 3, 4, 5, 6, 7, 8, 9]
        expected = [(1, 2), (3, 4), (5, 6), (7, 8)]
        actual = utils.every_two(raw_input)
        self.assertEqual(expected, actual)

    def test_interactive_confirm(self):
        message = {'m': ''} # Use dict since nonlocal missing in python 2.x
        confirm = 'Sure?'
        confirm_no = 'Sure? [y/N]: '
        confirm_yes = 'Sure? [Y/n]: '
        confirm_none = confirm_no
        def input_no(m):
            message['m'] = m
            return 'n'
        def input_none(m):
            message['m'] = m
            return ''
        def input_yes(m):
            message['m'] = m
            return 'y'

        tests = [
            { # Should be false when nothing input, default true.
                'expected': False,
                'default': False,
                'input_func': input_none,
                'confirm': confirm_no,
            },
            { # Should be true when true input, default true.
                'expected': True,
                'default': False,
                'input_func': input_yes,
                'confirm': confirm_no,
            },
            { # Should be false when false input, default true.
                'expected': False,
                'default': False,
                'input_func': input_no,
                'confirm': confirm_no,
            },
            { # Should be false when nothing input, default true.
                'expected': True,
                'default': True,
                'input_func': input_none,
                'confirm': confirm_yes,
            },
            { # Should be true when true input, default true.
                'expected': True,
                'default': True,
                'input_func': input_yes,
                'confirm': confirm_yes,
            },
            { # Should be false when false input, default true.
                'expected': False,
                'default': True,
                'input_func': input_no,
                'confirm': confirm_yes,
            },
        ]

        for test in tests:
            self.assertEqual(
                test['expected'],
                utils.interactive_confirm(
                    confirm, default=test['default'],
                    input_func=test['input_func']))
            self.assertEqual(test['confirm'], message['m'])

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

        # Test that deep linking to yaml files works.
        expected_deep_yaml = {
            'test': 'deep',
            'deep': 'deeper',
        }
        self.assertEqual(expected_deep_yaml, result['deep'])
        self.assertEqual(None, result['unfathomable'])

    def test_process_google_comments(self):
        # Google comment link.
        raw = '<div><a id="cmnt" href="https://grow.io/">Link</a></div>'
        expected = ''
        actual = utils.clean_html(raw)
        self.assertEqual(expected, actual)

        # Google footnote link.
        raw = '<sup><a id="ftnt" href="https://grow.io/">Link</a></sup>'
        expected = ''
        actual = utils.clean_html(raw)
        self.assertEqual(expected, actual)

    def test_safe_format(self):
        """Use modern text formatting on a string safely."""
        actual = utils.safe_format('Does it {0}?', 'work')
        self.assertEqual('Does it work?', actual)

        actual = utils.safe_format('Does it {work}?', work='blend')
        self.assertEqual('Does it blend?', actual)

        actual = utils.safe_format('Does it {ignore}?')
        self.assertEqual('Does it {ignore}?', actual)

    def test_slugify(self):
        """Slugify strings."""
        actual = utils.slugify('What\'s going: down 2 d@y')
        self.assertEqual('what-s-going:down-2-d-y', actual)

        actual = utils.slugify('Does it {work}')
        self.assertEqual('does-it-work', actual)

        actual = utils.slugify(u'Îñtérñåtîøñålization')
        self.assertEqual('internaationaalization', actual)

    def test_validate_name(self):
        with self.assertRaises(errors.BadNameError):
            utils.validate_name('//you/shall/not/pass')

        with self.assertRaises(errors.BadNameError):
            utils.validate_name('../you/shall/not/pass')

        with self.assertRaises(errors.BadNameError):
            utils.validate_name('/you/shall not/pass')

        utils.validate_name('c:\you\shall\pass')
        utils.validate_name('/you/shall/pass')
        utils.validate_name('you/shall/pass')
        utils.validate_name('./you/shall/pass')
        utils.validate_name(u'\xbe4/\xb05/\xb93')

    def test_version_enforcement(self):
        with mock.patch('grow.pods.pods.Pod.grow_version',
                        new_callable=mock.PropertyMock) as mock_version:
            gt_version = '>{0}'.format(semantic_version.Version(config.VERSION))
            mock_version.return_value = gt_version
            with self.assertRaises(updater.LatestVersionCheckError):
                _ = testing.create_test_pod()

    def test_walk(self):
        data = {
          'foo': 'bar',
          'bam': {
            'foo': 'bar2',
            'foo2': ['bar3', 'bar4'],
          }
        }

        actual = []
        callback = lambda item, key, node, parent_node: actual.append(item)
        utils.walk(data, callback)

        expected = ['bar', 'bar2', 'bar3', 'bar4']
        self.assertItemsEqual(expected, actual)

    def test_walk_empty(self):
        data = None

        actual = []
        callback = lambda item, key, node: actual.append(item)
        utils.walk(data, callback)

        expected = []
        self.assertItemsEqual(expected, actual)


if __name__ == '__main__':
    unittest.main()
