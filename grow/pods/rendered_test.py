from grow.pods import env
from grow.pods import errors
from grow.translations import locales
from grow.pods import pods
from grow.preprocessors import base
from grow.testing import testing
from protorpc import messages
import unittest


class RenderedTest(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path)

    def test_locale(self):
        controller, _ = self.pod.match('/fr/about/')
        fr_locale = locales.Locale.parse('fr')
        self.assertEqual(fr_locale, controller.locale)
        controller, _ = self.pod.match('/de_alias/about/')
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

    def test_render_error(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_file('/views/base.html', '{{doc.tulip()}}')
        fields = {
            'path': '/{base}/',
            'view': '/views/base.html',
        }
        pod.write_yaml('/content/collection/_blueprint.yaml', fields)
        pod.write_file('/content/collection/test.yaml', '')

        # Verify fails with correct error.
        controller, params = pod.match('/test/')
        with self.assertRaises(errors.BuildError):
            controller.render(params)

    def test_custom_jinja_extensions(self):
        controller, params = self.pod.match('/')
        html = controller.render(params)
        # Test pod uses a custom `|triplicate` filter on 'abcabcabc'
        self.assertIn('Custom Jinja Extension: abcabcabc', html)

    def test_list_concrete_paths(self):
        controller, _ = self.pod.match('/')
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

    def test_inject_ui(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/index.yaml', {})
        fields = {
            '$path': '/{base}/',
            '$view': '/views/base.html',
        }
        pod.write_yaml('/content/pages/_blueprint.yaml', fields)
        content = 'Test'
        pod.write_file('/views/base.html', content)
        ui_sentinel = '<script src="/_grow/ui/js/ui.min.js"></script>'

        # Verify UI not injected for normal pages.
        controller, params = pod.match('/index/')
        result = controller.render(params)
        self.assertNotIn(ui_sentinel, result)

        # Verify UI not injected unless injectable preprocessor is present.
        pod.env.name = env.Name.DEV
        controller, params = pod.match('/index/')
        result = controller.render(params)
        self.assertNotIn(ui_sentinel, result)

        # pylint: disable=abstract-method
        class DummyPreprocessor(base.BasePreprocessor):
            """Dummy preprocessor"""
            class Config(messages.Message):
                """Dummy config"""
                pass

            def get_edit_url(self, doc=None):
                """All edits are equal."""
                return 'https://example.com'

        config = DummyPreprocessor.Config()
        dummy_preprocessor = DummyPreprocessor(pod=pod, config=config)

        # Verify UI injected when preprocessor is present.
        controller, _ = pod.match('/index/')
        # pylint: disable=protected-access
        result = controller._inject_ui(content, dummy_preprocessor, dummy_preprocessor)
        self.assertIn(ui_sentinel, result)


if __name__ == '__main__':
    unittest.main()
