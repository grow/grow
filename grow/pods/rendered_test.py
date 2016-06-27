from grow.pods import locales
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class RenderedTest(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_locale(self):
        controller, params = self.pod.match('/fr/about/')
        fr_locale = locales.Locale.parse('fr')
        self.assertEqual(fr_locale, controller.locale)
        controller, params = self.pod.match('/de_alias/about/')
        de_locale = locales.Locale.parse('de')
        self.assertEqual(de_locale, controller.locale)
        self.assertEqual('de_alias', controller.locale.alias)

    def test_mimetype(self):
        controller, params = self.pod.match('/')
        self.assertEqual('text/html', controller.get_mimetype(params))
        controller, params = self.pod.match('/fr/about/')
        self.assertEqual('text/html', controller.get_mimetype(params))

    def test_render(self):
        controller, params = self.pod.match('/')
        controller.render(params)
        controller, params = self.pod.match('/fr/about/')
        controller.render(params)

    def test_custom_jinja_extensions(self):
        controller, params = self.pod.match('/')
        html = controller.render(params)
        # Test pod uses a custom `|triplicate` filter on 'abcabcabc'
        self.assertIn('Custom Jinja Extension: abcabcabc', html)

    def test_list_concrete_paths(self):
        controller, params = self.pod.match('/')
        self.assertEqual(['/'], controller.list_concrete_paths())

    def test_translation_recompilation(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'default_locale': 'en',
                'locales': ['ja'],
            },
        })
        pod.write_file('/views/base.html', '{{_("Hello")}}')
        fields = {
            'path': '/{base}/',
            'view': '/views/base.html',
            'localization': {
                'path': '/{locale}/{base}/',
            },
        }
        expected = 'Hello'
        translation = 'Translation'
        pod.write_yaml('/content/collection/_blueprint.yaml', fields)
        pod.write_file('/content/collection/test.yaml', '')
        pod.catalogs.extract()
        pod.catalogs.init(['ja'])
        ja_catalog = pod.catalogs.get('ja')
        self.assertIn(expected, pod.catalogs.get('ja'))
        ja_catalog[expected].string = translation

        # Verify untranslated.
        controller, params = pod.match('/ja/test/')
        content = controller.render(params)
        self.assertEqual(content, content)

        controller, params = pod.match('/test/')
        content = controller.render(params)
        self.assertEqual(expected, content)

        # Verify translated.
        ja_catalog.compile()
        controller, params = pod.match('/ja/test/')
        content = controller.render(params)
        self.assertEqual(translation, content)


if __name__ == '__main__':
    unittest.main()
