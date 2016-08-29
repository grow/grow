from . import pods
from . import static
from . import storage
from .. import preprocessors
from grow.common import utils
from grow.testing import testing
import jinja2
import mock
import os
import unittest


class PodTest(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

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

    def test_export(self):
        self.pod.export()

    def test_dump(self):
        paths = [
            '/about/index.html',
            '/app/root/static/somepath/de_alias/test-9b3051eb0c19358847e7c879275f810a.txt',
            '/app/static/file with spaces-d41d8cd98f00b204e9800998ecf8427e.txt',
            '/app/static/sym/test_sym-15918ecf75b208ad2decc78ec3caa95d.txt',
            '/app/static/test-db3f6eaa28bac5ae1180257da33115d8.txt',
            '/de_alias/about/index.html',
            '/de_alias/contact-us/index.html',
            '/de_alias/home/index.html',
            '/de_alias/html/index.html',
            '/de_alias/intro/index.html',
            '/de_alias/yaml_test/index.html',
            '/fi_ALL/about/index.html',
            '/fi_ALL/home/index.html',
            '/fi_ALL/html/index.html',
            '/fi_ALL/intro/index.html',
            '/fi_ALL/yaml_test/index.html',
            '/fil_ALL/about/index.html',
            '/fil_ALL/home/index.html',
            '/fil_ALL/html/index.html',
            '/fil_ALL/intro/index.html',
            '/fil_ALL/yaml_test/index.html',
            '/fr/about/index.html',
            '/fr/contact-us/index.html',
            '/fr/home/index.html',
            '/fr/html/index.html',
            '/fr/intro/index.html',
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
            '/it/yaml_test/index.html',
            '/post/newer/index.html',
            '/post/newest/index.html',
            '/post/older/index.html',
            '/post/oldest/index.html',
            '/public/file.txt',
            '/public/main.css',
            '/public/main.min.js',
            '/root/base/index.html',
            '/root/sitemap.xml',
            '/root/static/file-aa843134a2a113f7ebd5386c4d094a1a.min.js',
            '/root/static/file-d41d8cd98f00b204e9800998ecf8427e.txt',
            '/root/static-fingerprint/bc20b3c9007842b8e1f3c640b07f4e74/de_alias/fingerprinted.txt',
            '/root/static-fingerprint/961109f2e6cc139a8f6df6e3a307c247/fingerprinted.txt',
            '/yaml_test/index.html',
        ]
        result = self.pod.dump()
        self.maxDiff = None
        self.assertItemsEqual(paths, result)

    def test_list_deployments(self):
        self.pod.list_deployments()

    def test_get_home_doc(self):
        home_doc = self.pod.get_home_doc()
        doc = self.pod.get_doc('/content/pages/home.yaml')
        self.assertEqual(home_doc, doc)

    def test_get_static(self):
        static_file = self.pod.get_static('/public/file.txt')
        self.assertEqual('file', static_file.base)
        self.assertTrue(static_file.exists)
        self.assertRaises(
            static.BadStaticFileError, self.pod.get_static,
            '/bad-path/bad-file.txt')

    def test_list_statics(self):
        items = self.pod.list_statics('/public/')
        expected = [
            self.pod.get_static('/public/.dummy_dot_file'),
            self.pod.get_static('/public/file.txt'),
            self.pod.get_static('/public/main.css'),
            self.pod.get_static('/public/main.min.js'),
        ]
        for item in items:
            self.assertIn(item, expected)

    def test_list_jinja_extensions(self):
        items = self.pod.list_jinja_extensions()
        self.assertEqual(len(items), 1)
        # Custom extension is called Triplicate (see podspec.yaml in test pod)
        self.assertEqual(items[0].__name__, 'Triplicate')
        self.assertTrue(issubclass(items[0], jinja2.ext.Extension))

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
        self.assertEqual(self.pod._custom_preprocessor_value, 'testing123')


if __name__ == '__main__':
    unittest.main()
