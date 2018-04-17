"""Tests for the template tags and filters."""

import unittest
from grow.pods import pods
from grow import storage
from grow.templates import filters
from grow.testing import testing


class BuiltinsTestCase(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_shuffle_filter(self):
        words = ['foo', 'bar', 'baz']
        self.assertIn('foo', filters.shuffle_filter(None, words))

    def test_slug_filter(self):
        words = 'Foo Bar Baz'
        self.assertEqual('foo-bar-baz', filters.slug_filter(words))

        words = 'Foo\'s b@z b**'
        self.assertEqual('foo-s-b-z-b', filters.slug_filter(words))

        words = 'Foo: b@z b**'
        self.assertEqual('foo:b-z-b', filters.slug_filter(words))

    def test_json(self):
        controller, params = self.pod.match('/json_test/')
        html = controller.render(params)
        self.assertIn('key - value', html)
        self.assertIn('key2 - value2', html)

    def test_json_encoder(self):
        controller, params = self.pod.match('/json_test/')
        html = controller.render(params)
        self.assertIn('"$title": "Text Page"', html)
        self.assertIn('"$hidden": true', html)


if __name__ == '__main__':
    unittest.main()
