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

    def test_hash_filter(self):
        value = 'foobar'
        self.assertEqual(
            '3858f62230ac3c915f300c664312c63f',
            filters.hash_value(None, value, algorithm='md5'))
        self.assertEqual(
            '8843d7f92416211de9ebb963ff4ce28125932878',
            filters.hash_value(None, value, algorithm='sha1'))
        self.assertEqual(
            'de76c3e567fca9d246f5f8d3b2e704a38c3c5e258988ab525f941db8',
            filters.hash_value(None, value, algorithm='sha224'))
        self.assertEqual(
            '3c9c30d9f665e74d515c842960d4a451c83a0125fd3de7392d7b37231'
            'af10c72ea58aedfcdf89a5765bf902af93ecf06',
            filters.hash_value(None, value, algorithm='sha384'))
        self.assertEqual(
            '0a50261ebd1a390fed2bf326f2673c145582a6342d523204973d021933'
            '7f81616a8069b012587cf5635f6925f1b56c360230c19b273500ee013e'
            '030601bf2425',
            filters.hash_value(None, value, algorithm='sha512'))
        self.assertEqual(
            'c3ab8ff13720e8ad9047dd39466b3c8974e592c2fa383d4a3960714cae'
            'f0c4f2',
            filters.hash_value(None, value))

    def test_slug_filter(self):
        slug_filter = filters.slug_filter(self.pod)
        words = 'Foo Bar Baz'
        self.assertEqual('foo-bar-baz', slug_filter(words))

        words = 'Foo\'s b@z b**'
        self.assertEqual('foo-s-b-z-b', slug_filter(words))

        words = 'Foo: b@z b**'
        self.assertEqual('foo-b-z-b', slug_filter(words))

    def test_slug_filter_legacy(self):
        self.pod.enable(self.pod.FEATURE_OLD_SLUGIFY)
        slug_filter = filters.slug_filter(self.pod)
        words = 'Foo Bar Baz'
        self.assertEqual('foo-bar-baz', slug_filter(words))

        words = 'Foo\'s b@z b**'
        self.assertEqual('foo-s-b-z-b', slug_filter(words))

        words = 'Foo: b@z b**'
        self.assertEqual('foo:b-z-b', slug_filter(words))

    def test_json(self):
        self.pod.router.add_all(use_cache=False)
        html = testing.render_path(self.pod, '/json_test/')
        self.assertIn('key - value', html)
        self.assertIn('key2 - value2', html)

    def test_json_encoder(self):
        self.pod.router.add_all(use_cache=False)
        html = testing.render_path(self.pod, '/json_test/')
        self.assertIn('"$title": "Text Page"', html)
        self.assertIn('"$hidden": true', html)


if __name__ == '__main__':
    unittest.main()
