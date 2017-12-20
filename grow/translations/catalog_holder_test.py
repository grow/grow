# coding: utf-8
import unittest

from grow.pods import pods
from grow import storage
from grow.testing import testing


class CatalogsTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.pod.catalogs.compile()

    def test_list_locales(self):
        self.assertItemsEqual(
            ['de', 'fr', 'en', 'it', 'ja'],
            self.pod.catalogs.list_locales())

    def test_extract_options(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'extract': {
                    'localized': True,
                    'include_header': True,
                    'include_obsolete': True,
                    'fuzzy_matching': True,
                },
            },
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$title@': 'Collection Title',
            '$localization': {
                'locales': [
                    'de_DE',
                    'en_US',
                    'fr_FR',
                ],
            },
        })
        pod.write_yaml('/content/pages/page.yaml', {
            '$title@': 'Page Title',
        })
        pod.write_yaml('/content/pages/about.yaml', {
            '$title@': 'About Title',
            '$localization': {
                'locales': [
                    'fr_FR',
                ],
            },
        })
        pod.catalogs.extract()
        de_catalog = pod.catalogs.get('de_DE')
        self.assertNotIn('About Title', de_catalog)
        self.assertIn('Page Title', de_catalog)
        fr_catalog = pod.catalogs.get('fr_FR')
        self.assertIn('About Title', fr_catalog)

    def test_extract(self):
        _, template_catalogs = self.pod.catalogs.extract()
        template_catalog = template_catalogs[0]
        self.assertEqual(21, len(template_catalog))
        expected = [
            'Hello World!',
            'Hello World 2!',
            'Tagged String',
            'Tagged String in List 1',
            'Tagged String in List 2',
        ]
        for string in expected:
            self.assertIn(string, template_catalog)

        # Verify "include_obsolete" behavior.
        self.assertNotIn('foo', template_catalog)

        template_catalog.add('foo', 'bar')
        self.pod.catalogs.write_template(
            self.pod.catalogs.template_path, template_catalog)

        _, template_catalogs = self.pod.catalogs.extract(include_obsolete=True)
        template_catalog = template_catalogs[0]
        self.assertIn('foo', template_catalog)

        _, template_catalogs = self.pod.catalogs.extract(
            include_obsolete=False)
        template_catalog = template_catalogs[0]
        self.assertNotIn('foo', template_catalog)

        self.assertIn('string content tagged', template_catalog)
        self.assertNotIn('string content untagged', template_catalog)

    def test_extract_autocomments(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'localization': {
                'extract': {
                    'localized': True,
                },
            },
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$title@': 'Collection Title',
            '$localization': {
                'locales': [
                    'de_DE',
                    'en_US',
                ],
            },
        })
        pod.write_yaml('/content/pages/page.yaml', {
            '$title@': 'Page Title',
            '$title@#': 'Page Title Comment',
        })
        pod.write_yaml('/content/pages/about.yaml', {
            '$title@': 'About Title',
            'items@#': 'Items comment',
            'items@': [
                'one',
                'two',
                'three',
            ],
            'dict': {
                'key@#': 'object key comment',
                'key@': 'object key',
            },
        })
        pod.catalogs.extract()
        de_catalog = pod.catalogs.get('de_DE')

        # Extracted comment for string.
        self.assertIn('Page Title', de_catalog)
        message = de_catalog.get('Page Title')
        self.assertEqual('Page Title Comment', message.auto_comments[0])

        # Extracted comments for list items.
        items = ['one', 'two', 'three']
        for item in items:
            self.assertIn(item, de_catalog)
            message = de_catalog.get(item)
            self.assertEqual('Items comment', message.auto_comments[0])

        # Extracted comment for dict.
        self.assertIn('object key', de_catalog)
        message = de_catalog.get('object key')
        self.assertEqual('object key comment', message.auto_comments[0])

    def test_extract_podspec(self):
        # Verify global extract.
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'meta': {
                'title@': 'Test Title',
                'description@': 'Test Description',
            }
        })
        pod.catalogs.extract()
        self.assertIn('Test Title', pod.catalogs.get_template())
        self.assertIn('Test Description', pod.catalogs.get_template())
        # Verify localized extract.
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'meta': {
                'title@': 'Test Title',
                'description@': 'Test Description',
            },
            'localization': {
                'locales': [
                    'de',
                ],
            },
        })
        pod.catalogs.extract(localized=True)
        self.assertIn('Test Title', pod.catalogs.get('de'))

    def test_localized_extract(self):
        self.pod.catalogs.extract(localized=True)
        fr_catalog = self.pod.catalogs.get('fr')
        self.assertIn('Tagged localized title.', fr_catalog)
        self.assertNotIn('Tagged localized body.', fr_catalog)
        hi_catalog = self.pod.catalogs.get('hi_IN')
        self.assertIn('Tagged localized title.', hi_catalog)
        self.assertIn('Tagged localized body.', hi_catalog)

    def test_iter(self):
        locales = self.pod.catalogs.list_locales()
        for catalog in self.pod.catalogs:
            self.assertIn(str(catalog.locale), locales)

    def test_get(self):
        self.pod.catalogs.get('fr')

    def test_get_template(self):
        template = self.pod.catalogs.get_template()
        self.assertTrue(template.exists)
        template = self.pod.catalogs.get_template('messages.test.pot')
        self.assertFalse(template.exists)
        self.assertEqual(0, len(template))

    def test_compile(self):
        self.pod.catalogs.compile()

    def test_to_message(self):
        self.pod.catalogs.to_message()

    def test_init(self):
        self.pod.catalogs.init(['fr'])

    def test_update(self):
        self.pod.catalogs.update(['fr'])

    def test_filter(self):
        locales = ['de']
        catalogs = self.pod.catalogs.filter(
            out_path='./untranslated.po',
            locales=locales,
            localized=False)
        de_catalog = catalogs[0]
        self.assertEqual(3, len(de_catalog))

        paths = [
            '/content/pages/yaml_test.html',
        ]
        catalogs = self.pod.catalogs.filter(
            out_path='./untranslated.po',
            locales=locales,
            paths=paths,
            localized=False)
        de_catalog = catalogs[0]
        self.assertEqual(1, len(de_catalog))

    def test_filter_localized(self):
        locales = ['de', 'fr']
        catalogs = self.pod.catalogs.filter(
            out_dir='./untranslated/',
            locales=locales,
            localized=True)
        localized_de_catalog = catalogs[0]
        localized_fr_catalog = catalogs[1]
        fr_catalog = self.pod.catalogs.get('fr')
        self.assertEqual(3, len(localized_de_catalog))
        self.assertEqual(14, len(localized_fr_catalog))
        self.assertEqual(14, len(fr_catalog))

        paths = [
            '/content/pages/yaml_test.yaml',
            '/views/home.html',
        ]
        locales = ['de', 'fr']
        catalogs = self.pod.catalogs.filter(
            out_dir='./untranslated/',
            locales=locales,
            paths=paths,
            localized=True)
        localized_de_catalog = catalogs[0]
        localized_fr_catalog = catalogs[1]
        self.assertEqual(3, len(localized_de_catalog))
        self.assertEqual(14, len(localized_fr_catalog))

    def test_get_gettext_translations(self):
        self.pod.catalogs.get_gettext_translations('de')
        self.pod.catalogs.get_gettext_translations('it')

    def test_key_types(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        fields = {
            '$title@': 'Title',
            '$view': '/views/base.html',
            '$path': '/{base}/',
        }
        pod.write_yaml('/content/pages/_blueprint.yaml', fields)
        fields = {
            0: True,
            'key@': 'value',
        }
        pod.write_yaml('/content/pages/index.yaml', fields)
        pod.catalogs.extract()
        template = pod.catalogs.get_template()

        # Verify 'value' is added.
        self.assertIn('value', template)

        # Verify untagged non-sring isn't added.
        self.assertNotIn(True, template)

        # Verify tagged string in blueprint is added.
        self.assertIn('Title', template)


class _BaseExtractLocalizedTest(unittest.TestCase):
    # Both localized_pod and unlocalized_pod fixtures use these locales
    ALL_LOCALES = (
        'de',    # declared for podspec
        'fr',    # declared for blueprint
        'it',    # declared for a doc base part
        'ja',    # declared for a doc part
        'sv',    # declared for multi-locale doc parts
    )

    # Assert `message` appears in catalogs for all `locales`, and does NOT
    # appear in other catalogs in ALL_LOCALES
    def assertExtractedFor(self, pod, message, locales, inverse=False):
        # If `locales` is a string, assume single locale & coerce to iterable
        locales = (locales,) if isinstance(locales, basestring) else locales
        for locale in self.ALL_LOCALES:
            if locale in locales:
                if inverse:
                    self.assertNotIn(message, pod.catalogs.get(locale))
                else:
                    self.assertIn(message, pod.catalogs.get(locale))
            else:
                if inverse:
                    self.assertNotIn(message, pod.catalogs.get(locale))
                else:
                    self.assertNotIn(message, pod.catalogs.get(locale))

    def assertNotExtractedFor(self, pod, message, locales):
        return self.assertExtractedFor(pod, message, locales, inverse=True)


class ExtractLocalizedTest(_BaseExtractLocalizedTest):
    # setUpClass rather than setUp to only do this once & hence speed up tests
    # NOTE: Pods should NOT be modified by test cases

    @classmethod
    def setUpClass(cls):
        cls.localized_pod = testing.create_test_pod(
            'extract_localized/localized_pod')
        cls.localized_pod.catalogs.compile()
        cls.localized_pod.catalogs.extract(localized=True)
        cls.unlocalized_pod = testing.create_test_pod(
            'extract_localized/unlocalized_pod')
        cls.unlocalized_pod.catalogs.compile()
        cls.unlocalized_pod.catalogs.extract(localized=True)

    # NOTE: All tests should mix ASCII & non-ASCII chars

    # ================================================================
    # Document contexts (in /content/)
    # ================================================================

    # ------------------------------------------------
    # HTML document body
    # ------------------------------------------------

    def test_body_of_doc_part_extracted_for_part_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc part body in localized doc in localized collection in localized pöd',
            'ja')
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc part body in localized doc in unlocalized collection in localized pöd',
            'ja')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc part body in localized doc in localized collection in unlocalized pöd',
            'ja')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc part body in localized doc in unlocalized collection in unlocalized pöd',
            'ja')

    def test_body_of_multilocale_doc_part_extracted_for_part_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Multi-locale doc part body in localized doc in localized collection in localized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.localized_pod,
            u'Multi-locale doc part body in localized doc in unlocalized collection in localized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Multi-locale doc part body in localized doc in localized collection in unlocalized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Multi-locale doc part body in localized doc in unlocalized collection in unlocalized pöd',
            ['it', 'sv'])

    def test_body_of_doc_extracted_for_doc_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc in localized collection in localized pöd',
            'it')
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc in unlocalized collection in localized pöd',
            'it')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc in localized collection in unlocalized pöd',
            'it')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc in unlocalized collection in unlocalized pöd',
            'it')

    def test_body_of_base_doc_part_extracted_for_doc_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized multipart doc base part body in localized collection in localized pöd',
            ['ko'])
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized multipart doc base part body in unlocalized collection in localized pöd',
            ['ko'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized multipart doc base part body in localized collection in unlocalized pöd',
            ['ko'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized multipart doc base part body in unlocalized collection in unlocalized pöd',
            ['ko'])

    def test_body_of_doc_extracted_for_collection_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized doc body in localized collection in localized pöd',
            'fr')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Unlocalized doc body in localized collection in unlocalized pöd',
            'fr')

    def test_body_of_doc_extracted_for_podspec_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized doc body in unlocalized collection in localized pöd',
            'de')

    def test_body_of_doc_extracted_for_no_locales(self):
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Unlocalized doc body in unlocalized collection in unlocalized pöd',
            [])

    def test_body_of_md_doc_extracted(self):
        self.assertExtractedFor(
            self.localized_pod,
            'Untranslatable MD doc body',
            ['it'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            'Untranslatable MD doc body',
            ['it'])

    # ------------------------------------------------
    # YAML front matter of HTML/MD docs
    # ------------------------------------------------

    def test_doc_part_front_matter_extracted_for_part_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc part front matter in localized doc in localized collection in localized pöd',
            'ja')
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc part front matter in localized doc in unlocalized collection in localized pöd',
            'ja')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc part front matter in localized doc in localized collection in unlocalized pöd',
            'ja')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc part front matter in localized doc in unlocalized collection in unlocalized pöd',
            'ja')

    def test_doc_part_front_matter_extracted_for_multiple_part_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Multi-locale doc part front matter in localized doc in localized collection in localized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.localized_pod,
            u'Multi-locale doc part front matter in localized doc in unlocalized collection in localized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Multi-locale doc part front matter in localized doc in localized collection in unlocalized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Multi-locale doc part front matter in localized doc in unlocalized collection in unlocalized pöd',
            ['it', 'sv'])

    def test_base_doc_part_front_matter_extracted_for_doc_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized base doc front matter in localized collection in localized pöd',
            ['ko'])
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized base doc front matter in unlocalized collection in localized pöd',
            ['ko'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized base doc front matter in localized collection in unlocalized pöd',
            ['ko'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized base doc front matter in unlocalized collection in unlocalized pöd',
            ['ko'])

    def test_doc_front_matter_extracted_for_doc_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc front matter in localized collection in localized pöd',
            'it')
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc front matter in unlocalized collection in localized pöd',
            'it')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc front matter in localized collection in unlocalized pöd',
            'it')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc front matter in unlocalized collection in unlocalized pöd',
            'it')

    def test_doc_front_matter_extracted_for_collection_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized doc front matter in localized collection in localized pöd',
            'fr')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Unlocalized doc front matter in localized collection in unlocalized pöd',
            'fr')

    def test_doc_front_matter_extracted_for_podspec_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized doc front matter in unlocalized collection in localized pöd',
            'de')

    def test_doc_front_matter_extracted_for_no_locales(self):
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Unlocalized doc front matter in unlocalized collection in unlocalized pöd',
            [])

    # --------------------------------
    # YAML docs in collections
    # --------------------------------

    def test_yaml_part_extracted_for_own_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized yaml doc part in localized doc in localized collection in localized pöd',
            'ja')
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized yaml doc part in localized doc in unlocalized collection in localized pöd',
            'ja')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized yaml doc part in localized doc in localized collection in unlocalized pöd',
            'ja')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized yaml doc part in localized doc in unlocalized collection in unlocalized pöd',
            'ja')

    def test_yaml_part_in_unlocalized_doc_extracted_for_own_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc part in unlocalized doc in localized collection in localized pöd',
            'ja')
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc part in unlocalized doc in unlocalized collection in localized pöd',
            'pk')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized doc part in unlocalized doc in localized collection in unlocalized pöd',
            'ja')
        self.assertNotExtractedFor(
            self.unlocalized_pod,
            u'Localized doc part in unlocalized doc in unlocalized collection in unlocalized pöd',
            'ja')

    def test_multilocale_yaml_part_extracted_for_own_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Multi-locale yaml doc part in localized doc in localized collection in localized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.localized_pod,
            u'Multi-locale yaml doc part in localized doc in unlocalized collection in localized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Multi-locale yaml doc part in localized doc in localized collection in unlocalized pöd',
            ['it', 'sv'])
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Multi-locale yaml doc part in localized doc in unlocalized collection in unlocalized pöd',
            ['it', 'sv'])

    def test_yaml_doc_extracted_for_own_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized yaml doc in localized collection in localized pöd',
            'it')
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized yaml doc in unlocalized collection in localized pöd',
            'it')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized yaml doc in localized collection in unlocalized pöd',
            'it')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Localized yaml doc in unlocalized collection in unlocalized pöd',
            'it')

    def test_yaml_doc_extracted_for_collection_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized yaml doc in localized collection in localized pöd',
            'fr')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Unlocalized yaml doc in localized collection in unlocalized pöd',
            'fr')
        # Document is base + JA only.
        self.assertNotExtractedFor(
            self.localized_pod,
            u'Unlocalized base doc part in localized collection in localized pöd',
            'ja')
        self.assertNotExtractedFor(
            self.localized_pod,
            u'Unlocalized base doc part in localized collection in localized pöd',
            'fr')

    def test_yaml_doc_extracted_for_podspec_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized yaml doc in unlocalized collection in localized pöd',
            'de')
        # Document only specifies base doc part and $locale: ja, no
        # $localization.
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized base doc part in unlocalized collection in localized pöd',
            ['de', 'pl'])
        self.assertExtractedFor(
            self.localized_pod,
            u'Localized doc part in unlocalized doc in unlocalized collection in localized pöd',
            'pl')

    def test_yaml_doc_extracted_for_no_locales(self):
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Unlocalized yaml doc in unlocalized collection in unlocalized pöd',
            [])
        self.assertExtractedFor(
            self.localized_pod,
            u'Unlocalized base doc part in unlocalized collection in unlocalized pöd',
            [])

    # ------------------------------------------------
    # YAML files in /content/ root
    # ------------------------------------------------
    def test_yaml_in_content_root_extracted_for_podspec_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'YAML in content dir root in localized pöd',
            'de')

    def test_yaml_in_content_root_extracted_for_no_locales(self):
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'YAML in content dir root in unlocalized pöd',
            [])

    # ------------------------------------------------
    # CSV docs
    # ------------------------------------------------

    def test_csv_extracted_for_collection_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'CSV in localized collection in localized pöd',
            'fr')
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'CSV in localized collection in unlocalized pöd',
            'fr')

    def test_csv_extracted_for_podspec_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'CSV in unlocalized collection in localized pöd',
            'de')

    def test_csv_extracted_for_no_locales(self):
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'CSV in unlocalized collection in unlocalized pöd',
            [])

    # ================================================================
    # In templates (in /views/)
    # ================================================================

    def test_template_extracted_for_podspec_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Template in localized pöd',
            'de')

    def test_nested_template_extracted_for_podspec_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Template in subdir in localized pöd',
            'de')

    def test_template_extracted_for_no_locales(self):
        self.assertExtractedFor(
            self.unlocalized_pod,
            u'Template in unlocalized pöd',
            [])

    def test_nested_template_extracted_for_no_locales(self):
        self.assertExtractedFor(
            self.localized_pod,
            u'Template in subdir in unlocalized pöd',
            [])


class ExtractLocalizedWithExistingTest(_BaseExtractLocalizedTest):
    # Test behaviour when there are existing translations

    def test_excludes_obsolete_by_default(self):
        pod = testing.create_test_pod('extract_localized/localized_pod')
        pod.catalogs.compile()
        pod.catalogs.extract(localized=True, locales=['fr'])

        self.assertExtractedFor(pod, u'Existing message in localized pöd', [])
        # we don't use gettext syntax for obsolete translations
        for locale in self.ALL_LOCALES:
            self.assertFalse(pod.catalogs.get(locale).obsolete)

    def test_include_obsolete_option(self):
        pod = testing.create_test_pod('extract_localized/localized_pod')
        pod.catalogs.compile()
        pod.catalogs.extract(localized=True, locales=[
                             'fr'], include_obsolete=True)

        message = u'Existing message in localized pöd'
        translation = u'Existing FR translation in localized pöd'
        catalog = pod.catalogs.get('fr')

        self.assertExtractedFor(pod, message, ['fr'])
        self.assertEqual(catalog[message].string, translation)

        # we don't use gettext syntax for obsolete translations
        for locale in self.ALL_LOCALES:
            self.assertFalse(pod.catalogs.get(locale).obsolete)


class ExtractLocalizedSpecificLocalesTest(_BaseExtractLocalizedTest):

    def test_extract_localized_for_single_locale(self):
        localized_pod = testing.create_test_pod(
            'extract_localized/localized_pod')
        localized_pod.catalogs.compile()
        localized_pod.catalogs.extract(localized=True, locales=['it'])

        unlocalized_pod = testing.create_test_pod(
            'extract_localized/unlocalized_pod')
        unlocalized_pod.catalogs.compile()
        unlocalized_pod.catalogs.extract(localized=True, locales=['it'])

        # These strings are all relevant to both IT & SV, but should only be
        # extracted for IT
        italian_messages = (
            u'Multi-locale doc part body in localized doc in localized collection in localized pöd',
            u'Multi-locale doc part body in localized doc in unlocalized collection in localized pöd',
            u'Multi-locale doc part body in localized doc in localized collection in unlocalized pöd',
            u'Multi-locale doc part body in localized doc in unlocalized collection in unlocalized pöd',
            u'Multi-locale doc part front matter in localized doc in localized collection in localized pöd',
            u'Multi-locale doc part front matter in localized doc in unlocalized collection in localized pöd',
            u'Multi-locale doc part front matter in localized doc in localized collection in unlocalized pöd',
            u'Multi-locale doc part front matter in localized doc in unlocalized collection in unlocalized pöd',
            u'Multi-locale yaml doc part in localized doc in localized collection in localized pöd',
            u'Multi-locale yaml doc part in localized doc in unlocalized collection in localized pöd',
            u'Multi-locale yaml doc part in localized doc in localized collection in unlocalized pöd',
        )
        for message in italian_messages:
            if u'unlocalized pöd' in message:
                self.assertExtractedFor(unlocalized_pod, message, 'it')
            else:
                self.assertExtractedFor(localized_pod, message, 'it')

        # These are only relevant to FR, DE or no locales, so shouldn't be
        # extracted
        non_italian_messages = (
            u'Unlocalized doc body in localized collection in localized pöd',
            u'Unlocalized doc body in localized collection in unlocalized pöd',
            u'Unlocalized doc body in unlocalized collection in localized pöd',
            u'Unlocalized doc body in unlocalized collection in unlocalized pöd',
            u'Unlocalized doc front matter in localized collection in localized pöd',
            u'Unlocalized doc front matter in localized collection in unlocalized pöd',
            u'Unlocalized doc front matter in unlocalized collection in localized pöd',
            u'Unlocalized doc front matter in unlocalized collection in unlocalized pöd',
            u'Unlocalized yaml doc in localized collection in localized pöd',
            u'Unlocalized yaml doc in localized collection in unlocalized pöd',
            u'Unlocalized yaml doc in unlocalized collection in localized pöd',
            u'Unlocalized yaml doc in unlocalized collection in unlocalized pöd',
            u'Unlocalized pödspec',
        )

        for message in non_italian_messages:
            if u'unlocalized pöd' in message:
                self.assertExtractedFor(unlocalized_pod, message, [])
            else:
                self.assertExtractedFor(localized_pod, message, [])

    def test_extract_localized_for_multiple_locales(self):
        localized_pod = testing.create_test_pod(
            'extract_localized/localized_pod')
        localized_pod.catalogs.compile()
        localized_pod.catalogs.extract(
            localized=True, locales=['it', 'sv', 'de'])

        unlocalized_pod = testing.create_test_pod(
            'extract_localized/unlocalized_pod')
        unlocalized_pod.catalogs.compile()
        unlocalized_pod.catalogs.extract(
            localized=True, locales=['it', 'sv', 'de'])

        # These strings are all relevant to both IT & SV
        it_sv_messages = (
            u'Multi-locale doc part body in localized doc in localized collection in localized pöd',
            u'Multi-locale doc part body in localized doc in unlocalized collection in localized pöd',
            u'Multi-locale doc part body in localized doc in localized collection in unlocalized pöd',
            u'Multi-locale doc part body in localized doc in unlocalized collection in unlocalized pöd',
            u'Multi-locale doc part front matter in localized doc in localized collection in localized pöd',
            u'Multi-locale doc part front matter in localized doc in unlocalized collection in localized pöd',
            u'Multi-locale doc part front matter in localized doc in localized collection in unlocalized pöd',
            u'Multi-locale doc part front matter in localized doc in unlocalized collection in unlocalized pöd',
            u'Multi-locale yaml doc part in localized doc in localized collection in localized pöd',
            u'Multi-locale yaml doc part in localized doc in unlocalized collection in localized pöd',
            u'Multi-locale yaml doc part in localized doc in localized collection in unlocalized pöd',
        )
        for message in it_sv_messages:
            if u'unlocalized pöd' in message:
                self.assertExtractedFor(unlocalized_pod, message, ['it', 'sv'])
            else:
                self.assertExtractedFor(localized_pod, message, ['it', 'sv'])

        # These are only relevant to DE
        de_messages = (
            u'Unlocalized doc body in unlocalized collection in localized pöd',
            u'Unlocalized doc front matter in unlocalized collection in localized pöd',
            u'Unlocalized yaml doc in unlocalized collection in localized pöd',
        )

        for message in de_messages:
            if u'unlocalized pöd' in message:
                self.assertExtractedFor(unlocalized_pod, message, ['de'])
            else:
                self.assertExtractedFor(localized_pod, message, ['de'])

        # These are only relevant to FR or no locales, so shouldn't be
        # extracted
        fr_messages = (
            u'Unlocalized doc body in localized collection in localized pöd',
            u'Unlocalized doc body in localized collection in unlocalized pöd',
            u'Unlocalized doc body in unlocalized collection in unlocalized pöd',
            u'Unlocalized doc front matter in localized collection in localized pöd',
            u'Unlocalized doc front matter in localized collection in unlocalized pöd',
            u'Unlocalized doc front matter in unlocalized collection in unlocalized pöd',
            u'Unlocalized yaml doc in localized collection in localized pöd',
            u'Unlocalized yaml doc in localized collection in unlocalized pöd',
            u'Unlocalized yaml doc in unlocalized collection in unlocalized pöd',
            u'Unlocalized pödspec',
        )

        for message in fr_messages:
            if u'unlocalized pöd' in message:
                self.assertExtractedFor(unlocalized_pod, message, [])
            else:
                self.assertExtractedFor(localized_pod, message, [])

    def test_audit(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_yaml('/content/pages/_blueprint.yaml', {})
        pod.write_yaml('/content/pages/page.yaml', {
            'title': 'Untagged string',
            'subtitle@': 'Tagged string',
        })
        untagged_strings, _ = pod.catalogs.extract(audit=True)
        expected = [('/content/pages/page.yaml', 'Untagged string')]
        self.assertEqual(expected, untagged_strings)


if __name__ == '__main__':
    unittest.main()
