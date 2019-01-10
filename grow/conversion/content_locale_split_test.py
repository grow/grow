from grow.pods import pods
from grow import storage
from grow.testing import testing
import content_locale_split
import textwrap
import unittest


class ConversionDocumentTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.pod.write_yaml('/podspec.yaml', {})

    def test_convert_for_locale(self):
        input = textwrap.dedent("""
            foo@: bar
            foo@fr: baz
            foo@ja: bam
            """)

        # Converting for no locale removes all tagged fields.
        self.assertEquals(
            {'foo@': 'bar'},
            content_locale_split.ConversionDocument.convert_for_locale(input, None))

        # Converting for not specified locale removes all tagged fields.
        self.assertEquals(
            {'foo@': 'bar'},
            content_locale_split.ConversionDocument.convert_for_locale(input, 'en'))

        # Converting for specified locale updates and removes other tagged.
        self.assertEquals(
            {'foo@': 'baz'},
            content_locale_split.ConversionDocument.convert_for_locale(input, 'fr'))

        # Converting for specified locale updates and removes other tagged.
        self.assertEquals(
            {'foo@': 'bam'},
            content_locale_split.ConversionDocument.convert_for_locale(input, 'ja'))

    def test_determine_default_locale(self):
        input = textwrap.dedent("""
            name: Julie Yang
            """)
        self.assertEquals(
            None,
            content_locale_split.ConversionDocument.determine_default_locale(input))

        input = textwrap.dedent("""
            $localization:
              default_locale: de
            """)
        self.assertEquals(
            'de',
            content_locale_split.ConversionDocument.determine_default_locale(input))

        input = textwrap.dedent("""
            $localization:
              locales:
              - de
            """)
        self.assertEquals(
            None,
            content_locale_split.ConversionDocument.determine_default_locale(input))

    def test_determine_locales(self):
        # No locales returns empty.
        input = textwrap.dedent("""
            name: Julie Yang
            """)
        expected = ([], 'name: Julie Yang')
        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.determine_locales(
                input, default_locale='en'))

        # Non-default locale is preserved.
        input = textwrap.dedent("""
            $locale: de
            name: Julie Yang
            """)
        expected = (['de'], input.strip())
        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.determine_locales(
                input, default_locale='en', remove_locales=False))

        # Default locale is removed.
        input = textwrap.dedent("""
            $locale: de
            name: Julie Yang
            """)
        expected = ([], 'name: Julie Yang')
        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.determine_locales(
                input, default_locale='de'))

        # Default locale is removed.
        input = textwrap.dedent("""
            $locales:
            - de
            - fr
            - es
            name: Julie Yang
            """)
        expected = (['de', 'fr', 'es'], 'name: Julie Yang')
        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.determine_locales(
                input, default_locale='en'))

        # Locales are preserved.
        input = textwrap.dedent("""
            $locales:
            - de
            - fr
            - es
            name: Julie Yang
            """)
        expected = (['de', 'fr', 'es'], input.strip())
        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.determine_locales(input, remove_locales=False))

        # Nothing to see here.
        input = None
        expected = ([], None)
        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.determine_locales(input))

    def test_format_file(self):
        front_matter = textwrap.dedent("""
            name: Julie Yang
            foo: bar
            """).strip()
        content = textwrap.dedent("""
            Content reigns supreme.
            """).strip()

        expected = textwrap.dedent("""
            name: Julie Yang
            foo: bar
            """).lstrip()
        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.format_file(front_matter=front_matter))

        expected = textwrap.dedent("""
            Content reigns supreme.
            """).lstrip()

        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.format_file(content=content))

        expected = textwrap.dedent("""
            ---
            name: Julie Yang
            foo: bar
            ---
            Content reigns supreme.
            """).lstrip()

        self.assertEquals(
            expected,
            content_locale_split.ConversionDocument.format_file(
                front_matter=front_matter, content=content))

    def test_gather_for_locale(self):
        input = textwrap.dedent("""
            foo@: bar
            foo@fr: baz
            foo@ja: bam
            """).strip()

        # Gathering for no locale keeps all tagged fields.
        self.assertEquals(
            (input, {}),
            content_locale_split.ConversionDocument.gather_for_locale(input, None))

        # Gathering for not specified locale keeps all tagged fields.
        self.assertEquals(
            (input, {}),
            content_locale_split.ConversionDocument.gather_for_locale(input, 'en'))

        # Gathering for specified locale removes locale specific and keeps rest.
        self.assertEquals(
            ('foo@: bar\nfoo@ja: bam', {'foo@': 'baz'}),
            content_locale_split.ConversionDocument.gather_for_locale(input, 'fr'))

        # Gathering for specified locale removes locale specific and keeps rest.
        self.assertEquals(
            ('foo@: bar\nfoo@fr: baz', {'foo@': 'bam'}),
            content_locale_split.ConversionDocument.gather_for_locale(input, 'ja'))

    def test_default_locale_in_doc(self):
        self.pod.write_file('/content/test.md', textwrap.dedent("""
            ---
            name: Julie Yang
            foo@: bar
            $locales:
            - en_us
            - en_au
            - en_uk
            ---
            Content reigns supreme.
            ---
            $locale: ja
            foo@: baz
            ---
            Supreme the content reigns.
            ---
            $locales:
            - fr
            - ch
            foo@: bam
            foo@ch: zam
            ---
            Reigning content.
            """).lstrip())

        expected = {
            '/content/test.md': textwrap.dedent("""
                ---
                name: Julie Yang
                foo@: bar
                $locales:
                - en_au
                - en_uk
                ---
                Content reigns supreme.
                """).lstrip(),
            '/content/test@ja.md': textwrap.dedent("""
                ---
                foo@: baz
                ---
                Supreme the content reigns.
                """).lstrip(),
            '/content/test@fr.md': textwrap.dedent("""
                ---
                foo@: bam
                ---
                Reigning content.
                """).lstrip(),
            '/content/test@ch.md': textwrap.dedent("""
                ---
                foo@: zam
                ---
                Reigning content.
                """).lstrip(),
        }
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.md', 'en_us')
        doc.convert()
        for key, value in expected.iteritems():
            self.assertEquals(value, self.pod.read_file(key))

    def test_convert_with_empty_front_section(self):
        self.pod.write_file('/content/test.yaml', textwrap.dedent("""
                ---
                name: Julie Yang
                """).lstrip())


        expected = {
            '/content/test.yaml': textwrap.dedent("""
                name: Julie Yang
                """).lstrip(),
        }

        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.yaml', 'en_us')
        doc.convert()
        for key, value in expected.iteritems():
            self.assertEquals(value, self.pod.read_file(key))

    def test_convert_with_existing(self):
        self.pod.write_file('/content/test.md', textwrap.dedent("""
                ---
                name: Julie Yang
                ---
                Content reigns supreme.
                ---
                $locale: ja
                ---
                Supreme the content reigns.
                """).lstrip())
        self.pod.write_file('/content/test@ja.md', textwrap.dedent("""
                Supreme the content reigns.
                """).lstrip())

        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.md', 'en_us')

        with self.assertRaises(content_locale_split.LocaleExistsError):
            doc.convert()

    def test_convert_with_extended(self):
        self.pod.write_file('/content/test.yaml', textwrap.dedent("""
                name: Julie Yang
                ---
                $locales:
                - ja
                - fr
                foo: bar
                ---
                $locale: fr
                bar: faz
                """).lstrip())

        expected = {
            '/content/test.yaml': textwrap.dedent("""
                name: Julie Yang
                """).lstrip(),
            '/content/test@ja.yaml': textwrap.dedent("""
                foo: bar
                """).lstrip(),
            '/content/test@fr.yaml': textwrap.dedent("""
                bar: faz
                foo: bar
                """).lstrip(),
        }
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.yaml', 'en_us')
        doc.convert()

        for key, value in expected.iteritems():
            self.assertEquals(value, self.pod.read_file(key))

    def test_convert_with_missing_locale(self):
        self.pod.write_file('/content/test.yaml', textwrap.dedent("""
                name: Julie Yang
                ---
                foo:bar
                """).lstrip())

        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.yaml', 'en_us')

        with self.assertRaises(content_locale_split.LocaleMissingError):
            doc.convert()

    def test_convert_with_gather(self):
        self.pod.write_file('/content/test.md', textwrap.dedent("""
                ---
                name: Julie Yang
                bar@: tri
                bar@es: pep
                bar@fr: pip
                bar@ja: tes
                ---
                Content reigns supreme.
                ---
                $locale: ja
                ---
                Supreme the content reigns.
                ---
                $locale: fr
                ---
                Reigning content.
                """).lstrip())

        expected = {
            '/content/test.md': textwrap.dedent("""
                ---
                name: Julie Yang
                bar@: tri
                bar@es: pep
                ---
                Content reigns supreme.
                """).lstrip(),
            '/content/test@ja.md': textwrap.dedent("""
                ---
                bar@: tes
                ---
                Supreme the content reigns.
                """).lstrip(),
            '/content/test@fr.md': textwrap.dedent("""
                ---
                bar@: pip
                ---
                Reigning content.
                """).lstrip(),
        }
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.md', 'en_us')
        doc.convert()

        for key, value in expected.iteritems():
            self.assertEquals(value, self.pod.read_file(key))

    def test_convert_with_gather_array(self):
        self.pod.write_file('/content/test.md', textwrap.dedent("""
                ---
                name: Julie Yang
                bar:
                - title: bar
                  title@fr: rab
                  foo: fed
                - title: bam
                  title@fr: mab
                  foo: dew
                - title: baz
                  foo: tee
                ---
                Content reigns supreme.
                ---
                $locale: ja
                ---
                Supreme the content reigns.
                ---
                $locale: fr
                ---
                Reigning content.
                """).lstrip())

        expected = {
            '/content/test.md': textwrap.dedent("""
                ---
                name: Julie Yang
                bar:
                - title: bar
                  foo: fed
                - title: bam
                  foo: dew
                - title: baz
                  foo: tee
                ---
                Content reigns supreme.
                """).lstrip(),
            '/content/test@ja.md': textwrap.dedent("""
                Supreme the content reigns.
                """).lstrip(),
            '/content/test@fr.md': textwrap.dedent("""
                ---
                bar:
                - title: rab
                  foo: fed
                - title: mab
                  foo: dew
                - title: baz
                  foo: tee
                ---
                Reigning content.
                """).lstrip(),
        }
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.md', 'en_us')
        doc.convert()

        for key, value in expected.iteritems():
            self.assertEquals(value, self.pod.read_file(key))

    def test_convert_with_gather_trailing(self):
        self.pod.write_file('/content/test.md', textwrap.dedent("""
                ---
                name: Julie Yang
                grr:
                  foo: tas
                  foo@es: sep
                  foo@fr: gli
                  foo@ja: min
                ---
                Content reigns supreme.
                ---
                $locale: ja
                ---
                Supreme the content reigns.
                ---
                $locale: fr
                ---
                Reigning content.
                """).lstrip())

        expected = {
            '/content/test.md': textwrap.dedent("""
                ---
                name: Julie Yang
                grr:
                  foo: tas
                  foo@es: sep
                ---
                Content reigns supreme.
                """).lstrip(),
            '/content/test@ja.md': textwrap.dedent("""
                ---
                grr:
                  foo: min
                ---
                Supreme the content reigns.
                """).lstrip(),
            '/content/test@fr.md': textwrap.dedent("""
                ---
                grr:
                  foo: gli
                ---
                Reigning content.
                """).lstrip(),
        }
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/test.md', 'en_us')
        doc.convert()

        for key, value in expected.iteritems():
            self.assertEquals(value, self.pod.read_file(key))

    def test_split(self):
        # Two part document.
        self.pod.write_file('/content/something.md', textwrap.dedent("""
            ---
            name: Julie Yang
            foo@: bar
            ---
            Content reigns supreme.
            ---
            $locale: ja
            foo@: baz
            ---
            Supreme the content reigns.
            """).lstrip())

        expected = [
            (textwrap.dedent("""
                    name: Julie Yang
                    foo@: bar
                    """).strip(), 'Content reigns supreme.'),
            (textwrap.dedent("""
                    $locale: ja
                    foo@: baz
                    """).strip(), 'Supreme the content reigns.'),
        ]
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/something.md', 'en_us')
        self.assertEquals(expected, list(doc.split()))

        # Empty front matter document.
        self.pod.write_file('/content/something.md', textwrap.dedent("""
            ---
            ---
            Content reigns supreme.
            """).lstrip())

        expected = [
            (None, 'Content reigns supreme.'),
        ]
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/something.md', 'en_us')
        self.assertEquals(expected, list(doc.split()))

        # Missing front matter document.
        self.pod.write_file('/content/something.md', textwrap.dedent("""
            Content reigns supreme.
            """).lstrip())

        expected = [
            (None, 'Content reigns supreme.'),
        ]
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/something.md', 'en_us')
        self.assertEquals(expected, list(doc.split()))

        # Yaml document.
        self.pod.write_file('/content/something.yaml', textwrap.dedent("""
            name: Julie Yang
            foo: bar
            ---
            $locale: ja
            foo: baz
            """).lstrip())

        expected = [
            (textwrap.dedent("""
                    name: Julie Yang
                    foo: bar
                    """).strip(), None),
            (textwrap.dedent("""
                    $locale: ja
                    foo: baz
                    """).strip(), None),
        ]
        doc = content_locale_split.ConversionDocument(
            self.pod, '/content/something.yaml', 'en_us')
        self.assertEquals(expected, list(doc.split()))


if __name__ == '__main__':
    unittest.main()
