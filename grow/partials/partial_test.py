"""Test the pod partial."""

import unittest
from grow import storage
from grow.pods import pods
from grow.testing import testing


class PartialTestCase(unittest.TestCase):
    """Tests for partials."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_editor_config(self):
        """Test that editor configuration is read correctly."""
        partials = self.pod.partials
        partial = partials.get_partial('hero')
        expected = {
            'label': 'Hero',
            'editor': {
                'fields': [
                    {
                        'type': 'text',
                        'key': 'title',
                        'label': 'Hero Title'
                    }, {
                        'type': 'text',
                        'key': 'subtitle',
                        'label': 'Hero Subtitle'
                    },
                    {
                        'type': 'markdown',
                        'key': 'description',
                        'label': 'Description'
                    },
                ],
            },
        }
        self.assertEquals(expected, partial.editor_config)


if __name__ == '__main__':
    unittest.main()
