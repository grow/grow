"""Tests for the document fields."""

import unittest
from grow.editor import editor_config


class EditorConfigTestCase(unittest.TestCase):
    """Test the editor configuration."""

    def test_fields(self):
        """Fields get pulled from config."""

        config = editor_config.EditorConfig({
            'fields': [
                {
                    'type': 'textarea',
                    'key': 'meta.description',
                    'label': 'Description',
                },
                {
                    'type': 'partials',
                    'key': 'partials',
                    'label': 'Partials',
                },
            ],
        })

        self.assertEquals([], config.partials)
        self.assertEquals([
            {
                'type': 'textarea',
                'key': 'meta.description',
                'label': 'Description',
            },
            {
                'type': 'partials',
                'key': 'partials',
                'label': 'Partials',
            },
        ], config.fields)

    def test_partials(self):
        """Partials get pulled from config."""

        config = editor_config.EditorConfig({
            'partials': ['hero'],
        })

        self.assertEquals(['hero'], config.partials)
        self.assertEquals([], config.fields)

    def test_export(self):
        """Settings get exported into object."""

        config = editor_config.EditorConfig()
        config.partials = ['hero']
        config.fields = [
            {
                'type': 'textarea',
                'key': 'meta.description',
                'label': 'Description',
            },
            {
                'type': 'partials',
                'key': 'partials',
                'label': 'Partials',
            },
        ]

        self.assertEquals({
            'fields': [
                {
                    'type': 'textarea',
                    'key': 'meta.description',
                    'label': 'Description',
                },
                {
                    'type': 'partials',
                    'key': 'partials',
                    'label': 'Partials',
                },
            ],
            'partials': ['hero'],
        }, config.export())


if __name__ == '__main__':
    unittest.main()
