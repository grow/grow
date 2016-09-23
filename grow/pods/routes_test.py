from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest
import webob.exc


class RoutesTest(unittest.TestCase):

    def setUp(self):
        self.maxDiff = None
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_match(self):
        controller, params = self.pod.match('/')
        controller.render(params)
        controller, params = self.pod.match('/fr/about/')
        controller.render(params)
        controller, params = self.pod.match('/de_alias/about/')
        controller.render(params)
        self.assertRaises(webob.exc.HTTPNotFound, self.pod.match, '/dummy/')
        controller, params = self.pod.match('/app/static/file with spaces.txt')

    def test_list_concrete_paths(self):
        expected = [
            '/',
            '/about/',
            '/app/root/static/somepath/de_alias/test-9b3051eb0c19358847e7c879275f810a.txt',
            '/app/static/file with spaces-d41d8cd98f00b204e9800998ecf8427e.txt',
            '/app/static/sym/test_sym-15918ecf75b208ad2decc78ec3caa95d.txt',
            '/app/static/test-db3f6eaa28bac5ae1180257da33115d8.txt',
            '/de_alias/about/',
            '/de_alias/contact-us/',
            '/de_alias/home/',
            '/de_alias/html/',
            '/de_alias/intro/',
            '/de_alias/yaml_test/',
            '/fi_ALL/about/',
            '/fi_ALL/home/',
            '/fi_ALL/html/',
            '/fi_ALL/intro/',
            '/fi_ALL/yaml_test/',
            '/fil_ALL/about/',
            '/fil_ALL/home/',
            '/fil_ALL/html/',
            '/fil_ALL/intro/',
            '/fil_ALL/yaml_test/',
            '/fr/about/',
            '/fr/contact-us/',
            '/fr/home/',
            '/fr/html/',
            '/fr/intro/',
            '/fr/yaml_test/',
            '/html/',
            '/intl/de_alias/localized/',
            '/intl/de_alias/multiple-locales/',
            '/intl/en/localized/',
            '/intl/en_gb/localized/',
            '/intl/en_pk/localized-view/',
            '/intl/fr/localized/',
            '/intl/fr/multiple-locales/',
            '/intl/hi_in/localized/',
            '/intl/it/multiple-locales/',
            '/intl/ja/localized/',
            '/intl/tr_tr/localized-view/',
            '/intro/',
            '/it/about/',
            '/it/contact-us/',
            '/it/home/',
            '/it/html/',
            '/it/intro/',
            '/it/yaml_test/',
            '/post/newer/',
            '/post/newest/',
            '/post/older/',
            '/post/oldest/',
            '/public/file.txt',
            '/public/main.css',
            '/public/main.min.js',
            '/root/base/',
            '/root/sitemap.xml',
            '/root/static/file-aa843134a2a113f7ebd5386c4d094a1a.min.js',
            '/root/static/file-d41d8cd98f00b204e9800998ecf8427e.txt',
            '/root/static-fingerprint/bc20b3c9007842b8e1f3c640b07f4e74/de_alias/fingerprinted.txt',
            '/root/static-fingerprint/961109f2e6cc139a8f6df6e3a307c247/fingerprinted.txt',
            '/yaml_test/',
        ]
        result = self.pod.routes.list_concrete_paths()
        self.assertItemsEqual(expected, result)

    def test_subcollection_paths(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en',
                'locales': [
                    'de',
                    'en',
                ]
            }
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$view': '/views/base.html',
            '$path': '/{base}/',
            '$localization': {
                'path': '/{locale}/{base}/',
            }
        })
        pod.write_yaml('/content/pages/page.yaml', {
            '$title': 'Page',
        })
        pod.write_yaml('/content/pages/sub/_blueprint.yaml', {
            '$view': '/views/base.html',
            '$path': '/sub/{base}/',
            '$localization': {
                'path': '/sub/{locale}/{base}/',
            }
        })
        pod.write_yaml('/content/pages/sub/page.yaml', {
            '$title': 'Sub Page',
        })

        # Verify subcollections are included in pod.list_collections.
        collection_objs = pod.list_collections()
        pages = pod.get_collection('pages')
        sub = pod.get_collection('pages/sub')
        expected = [pages, sub]
        self.assertEqual(expected, collection_objs)

        # Verify subcollection docs are not included in collection.docs.
        expected = [
            pod.get_doc('/content/pages/page.yaml'),
            pod.get_doc('/content/pages/page.yaml', locale='de'),
        ]
        docs = pages.docs(recursive=False)
        self.assertEqual(expected, list(docs))

        paths = pod.routes.list_concrete_paths()
        expected=  ['/sub/page/', '/de/page/', '/sub/de/page/', '/page/']
        self.assertEqual(expected, paths)


if __name__ == '__main__':
    unittest.main()
