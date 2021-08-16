# coding: utf8
"""Tests for the common utility methods."""

import unittest
import mock
import semantic_version
from grow.testing import testing
from grow.sdk import sdk_utils
from grow.pods import errors
from . import utils


class UtilsTestCase(unittest.TestCase):

    def test_clean_google_href(self):
        # Test without a match.
        raw_input = '<a href="https://grow.dev/">Link</a>'
        expected = '<a href="https://grow.dev/">Link</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

        # Test with ?q=
        raw_input = '<a href="https://www.google.com/url?q=https%3A%2F%2Fgrow.dev%2Fdocs%2F">Google Search</a>'
        expected = '<a href="https://grow.dev/docs/">Google Search</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

        # Test with &q=
        raw_input = '<a href="https://www.google.com/url?sa=t&q=https%3A%2F%2Fgrow.dev%2Fdocs%2F">Google Search</a>'
        expected = '<a href="https://grow.dev/docs/">Google Search</a>'
        actual = utils.clean_html(raw_input)
        self.assertEqual(expected, actual)

    def test_clean_html_markdown(self):
        # Test without a match.
        raw_input = '<a href="https://grow.dev/">Link</a>'
        expected = '[Link](https://grow.dev/)'
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

    def test_parse_yaml_localized(self):
        """Parsing yaml with a locale correctly loads the localized values."""
        pod = testing.create_test_pod()
        content = pod.read_file('/data/constructors.yaml')

        # Base unlocalized works.
        result = utils.parse_yaml(content, pod=pod)
        expected = 'base_value'
        self.assertEqual(expected, result['localized'])

        # Other locals correctly localize.
        result = utils.parse_yaml(content, pod=pod, locale='es')
        expected = 'es_value'
        self.assertEqual(expected, result['localized'])

    def test_parse_yaml_strings(self):
        """Parsing using strings constructor."""
        pod = testing.create_test_pod()
        content = pod.read_file('/data/string.yaml')

        # Base strings.
        result = utils.parse_yaml(content, pod=pod)
        self.assertEqual('Sun', result['sun'])
        self.assertEqual('Mars', result['mars'])

        # Localized strings.
        result = utils.parse_yaml(content, pod=pod, locale='es')
        self.assertEqual('Sol', result['sun'])
        self.assertEqual('Marte', result['mars'])

    def test_parse_deep_yaml_strings(self):
        """Parsing using yaml that contains strings constructor."""
        pod = testing.create_test_pod()
        content = pod.read_file('/data/constructors.yaml')

        # Base strings.
        result = utils.parse_yaml(content, pod=pod)
        self.assertEqual('Sun', result['deep_strings']['sun'])
        self.assertEqual('Mars', result['deep_strings']['mars'])

        # Localized strings.
        result = utils.parse_yaml(content, pod=pod, locale='es')
        self.assertEqual('Sol', result['deep_strings']['sun'])
        self.assertEqual('Marte', result['deep_strings']['mars'])

    def test_process_google_comments(self):
        # Google comment link.
        raw = '<div><a id="cmnt" href="https://grow.dev/">Link</a></div>'
        expected = ''
        actual = utils.clean_html(raw)
        self.assertEqual(expected, actual)

        # Google footnote link.
        raw = '<sup><a id="ftnt" href="https://grow.dev/">Link</a></sup>'
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

        actual = utils.slugify('Îñtérñåtîøñålization')
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
        utils.validate_name('\xbe4/\xb05/\xb93')

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

        expected = sorted(['bar', 'bar2', 'bar3', 'bar4'])
        self.assertEqual(expected, sorted(actual))

    def test_walk_empty(self):
        data = None

        actual = []
        callback = lambda item, key, node: actual.append(item)
        utils.walk(data, callback)

        expected = []
        self.assertEqual(expected, sorted(actual))


if __name__ == '__main__':
    unittest.main()
