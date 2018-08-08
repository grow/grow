"""Tests for Grow podspec."""

import unittest

from grow.pod import podspec


class PodspecTest(unittest.TestCase):
    """Grow pod specification testing."""

    def test_locale_aliases(self):
        """Locale alias cache."""
        spec = podspec.PodSpec({
            'localization': {
                'locales': [
                    'en_US',
                    'en_AU',
                    'en_GB',
                ],
                'aliases': {
                    'en_US': 'en_ALL',
                }
            },
        })

        aliases = spec.locale_aliases
        self.assertEqual('en_ALL', aliases.alias_from_locale('en_US'))


if __name__ == '__main__':
    unittest.main()
