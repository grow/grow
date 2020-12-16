"""Tests for the grow pod."""

import os
import unittest
import mock
import jinja2
from grow import preprocessors
from grow import storage
from grow.testing import testing
from . import pods
from grow.routing import router


class PodTest(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_disable(self):
        self.assertTrue(self.pod.is_enabled('testing'))
        self.pod.disable('testing')
        self.assertFalse(self.pod.is_enabled('testing'))

    def test_enable(self):
        self.assertFalse(self.pod.is_enabled(self.pod.FEATURE_TRANSLATION_STATS))
        self.pod.enable(self.pod.FEATURE_TRANSLATION_STATS)
        self.assertTrue(self.pod.is_enabled(self.pod.FEATURE_TRANSLATION_STATS))

    def test_experiment_no_config(self):
        """Experiments with true value are enabled with no config."""
        self.assertTrue(self.pod.experiments.is_enabled('test_a'))
        self.assertEqual({}, self.pod.experiments.config('test_a').export())

    def test_experiment_config(self):
        """Experiments with configs are enabled with config."""
        self.assertTrue(self.pod.experiments.is_enabled('test_b'))
        self.assertEqual(
            {'value': 'foo'}, self.pod.experiments.config('test_b').export())

    def test_eq(self):
        pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.assertEqual(self.pod, pod)

    def test_list_dir(self):
        dirpath = os.path.join(self.dir_path, 'content')
        num_files = 0
        for root, dirs, files in os.walk(dirpath):
            for filename in files:
                num_files += 1
        actual = self.pod.list_dir('/content')
        self.assertEqual(len(actual), num_files)

    def test_read_file(self):
        content = self.pod.read_file('/README.md')
        path = os.path.join(self.dir_path, 'README.md')
        expected_content = open(path).read()
        self.assertEqual(expected_content, content)

    def test_write_file(self):
        path = '/dummy.yaml'
        self.pod.write_file(path, 'foo')
        content = self.pod.read_file(path)
        self.assertEqual('foo', content)

        self.pod.write_file(path, 'bar')
        content = self.pod.read_file(path)
        self.assertEqual('bar', content)

    def test_list_collections(self):
        self.pod.list_collections()

    def test_clean_pod_path(self):
        self.assertEqual(
            '/content/pages/index.yaml',
            self.pod.clean_pod_path('/content/pages/index.yaml'))
        self.assertEqual(
            '/content/pages/index.yaml',
            self.pod.clean_pod_path('content/pages/index.yaml'))

    def test_export(self):
        for _ in self.pod.export():
            pass

    def test_dump(self):
        paths = sorted([
            '/about/index.html',
            '/app/static/intl/de/test-7d0db06e20c10ad191b9ab260fa9aad1492f94884e10fd99e5cff31a10536232.txt',
            '/app/static/file with spaces-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.txt',
            '/app/static/sym/test_sym-d67d5d70e71058c29a3f80433c71323bcc15f221d67889517f08f97c324c7f8a.txt',
            '/app/static/test-180e03ea719ad14b0e02701048db567e231eb6fd0a23b6359f068b1e8bef135b.txt',
            '/de_alias/about/index.html',
            '/de_alias/contact-us/index.html',
            '/de_alias/home/index.html',
            '/de_alias/html/index.html',
            '/de_alias/intro/index.html',
            '/de_alias/json_test/index.html',
            '/de_alias/yaml_test/index.html',
            '/fi_ALL/about/index.html',
            '/fi_ALL/home/index.html',
            '/fi_ALL/html/index.html',
            '/fi_ALL/intro/index.html',
            '/fi_ALL/json_test/index.html',
            '/fi_ALL/yaml_test/index.html',
            '/fil_ALL/about/index.html',
            '/fil_ALL/home/index.html',
            '/fil_ALL/html/index.html',
            '/fil_ALL/intro/index.html',
            '/fil_ALL/json_test/index.html',
            '/fil_ALL/yaml_test/index.html',
            '/fr/about/index.html',
            '/fr/contact-us/index.html',
            '/fr/home/index.html',
            '/fr/html/index.html',
            '/fr/intro/index.html',
            '/fr/json_test/index.html',
            '/fr/yaml_test/index.html',
            '/html/index.html',
            '/index.html',
            '/intl/de_alias/localized/index.html',
            '/intl/de_alias/multiple-locales/index.html',
            '/intl/en/localized/index.html',
            '/intl/en_gb/localized/index.html',
            '/intl/en_pk/localized-view/index.html',
            '/intl/fr/localized/index.html',
            '/intl/fr/multiple-locales/index.html',
            '/intl/hi_in/localized/index.html',
            '/intl/it/multiple-locales/index.html',
            '/intl/ja/localized/index.html',
            '/intl/tr_tr/localized-view/index.html',
            '/intro/index.html',
            '/it/about/index.html',
            '/it/contact-us/index.html',
            '/it/home/index.html',
            '/it/html/index.html',
            '/it/intro/index.html',
            '/it/json_test/index.html',
            '/it/yaml_test/index.html',
            '/post/newer/index.html',
            '/post/newest/index.html',
            '/post/older/index.html',
            '/post/oldest/index.html',
            '/public/file.txt',
            '/public/main.css',
            '/public/main.min.js',
            '/public/dir/file.txt',
            '/root/base/index.html',
            '/root/sitemap.xml',
            '/root/static/file-583581c807375a01ee310e606408c385701202dced0a8f0e261d280d0f3d6ce7.min.js',
            '/root/static/file-e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855.txt',
            '/root/static-fingerprint/cf30133e9599fd2e425291fe89c2f0975ecee8014d2739efbab2d5810a437173/intl/de/fingerprinted.txt',
            '/root/static-fingerprint/874ef0b000c76b0695b5af38aeb2da28c2365db07545163615e590a21cb0cbc0/fingerprinted.txt',
            '/shared/test-b.txt',
            '/shared/test-a.txt',
            '/shared/intl/test-a.txt',
            '/shared/intl/test-b.txt',
            '/json_test/index.html',
            '/yaml_test/index.html',
        ])
        self.pod.router.add_all(use_cache=False)
        self.maxDiff = None

        result = sorted([doc.path for doc in self.pod.dump()])
        self.assertEqual(paths, result)

    def test_list_deployments(self):
        self.pod.list_deployments()

    def test_get_home_doc(self):
        home_doc = self.pod.get_home_doc()
        doc = self.pod.get_doc('/content/pages/home.yaml')
        self.assertEqual(home_doc, doc)

    def test_get_static(self):
        static_file = self.pod.get_static('/public/file.txt')
        self.assertTrue(static_file.exists)
        self.assertRaises(
            router.MissingStaticConfigError, self.pod.get_static,
            '/bad-path/bad-file.txt')

    def test_list_statics(self):
        items = self.pod.list_statics('/public/')
        expected = [
            self.pod.get_static('/public/dir/file.txt'),
            self.pod.get_static('/public/file.txt'),
            self.pod.get_static('/public/main.css'),
            self.pod.get_static('/public/main.min.js'),
        ]
        for item in items:
            self.assertIn(item, expected)

    def test_list_statics_hidden(self):
        items = self.pod.list_statics('/public/', include_hidden=True)
        expected = [
            self.pod.get_static('/public/dir/.dummy_dot_file'),
            self.pod.get_static('/public/dir/file.txt'),
            self.pod.get_static('/public/.dummy_dot_file'),
            self.pod.get_static('/public/file.txt'),
            self.pod.get_static('/public/main.css'),
            self.pod.get_static('/public/main.min.js'),
        ]
        for item in items:
            self.assertIn(item, expected)

    def test_list_jinja_extensions(self):
        items = self.pod.list_jinja_extensions()
        self.assertEqual(len(items), 2)
        # Custom extension is called Triplicate (see podspec.yaml in test pod)
        self.assertEqual(items[1].__name__, 'Triplicate')
        self.assertTrue(issubclass(items[1], jinja2.ext.Extension))

    def test_invalid_jinja_extension(self):
        # Make sure an invalid jinja2 exensions config throws an error
        with mock.patch.dict(self.pod.yaml, {'extensions': {'jinja2': ['invalid/path']}}):
            with self.assertRaises(ImportError):
                self.pod.list_jinja_extensions()

    def test_list_preprocessors(self):
        items = self.pod.list_preprocessors()
        self.assertEqual(len(items), 1)
        # see podspec.yaml in test pod
        self.assertEqual(items[0].__class__.__name__, 'CustomPreprocessor')
        self.assertTrue(isinstance(items[0], preprocessors.base.BasePreprocessor))
        # Calling again should get the same results (list is refreshed on each
        # call, so want to make sure it isn't extended with duplicates)
        self.assertEqual(len(self.pod.list_preprocessors()), 1)

    def test_custom_preprocessor(self):
        self.pod.preprocess(['custom'])
        # pylint: disable=no-member
        self.assertEqual(self.pod._custom_preprocessor_value, 'testing123')

    def test_dump_static_files_without_extension(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'static_dirs': [{
                'static_dir': '/source/media/',
                'serve_at': '/static/',
            }],
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
        })
        pod.write_yaml('/content/pages/foo.yaml', {
            '$title': 'Foo',
        })
        pod.write_file('/source/media/file.txt', 'file')
        pod.write_file('/source/media/extensionless', 'file')
        pod.write_file('/views/base.html', '{{doc.html|safe}}')
        pod.router.add_all(use_cache=False)

        # Verify dump appends suffix.
        expected = sorted([
            '/foo/index.html',
            '/static/file.txt',
            '/static/extensionless',
        ])
        paths = []
        for rendered_doc in pod.dump():
            paths.append(rendered_doc.path)
        self.assertEqual(expected, sorted(paths))


if __name__ == '__main__':
    unittest.main()
