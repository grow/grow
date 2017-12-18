"""Tests for the document front matter."""

import unittest
import textwrap
from grow.testing import testing
from grow.documents import document_front_matter
from grow.pods import pods
from grow import storage


class DocumentFrontmatterTestCase(unittest.TestCase):
    """Tests for document front matter."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_bad_format(self):
        """Tests case for badly formatted raw content."""
        doc = self.pod.get_doc('/content/pages/html.html')
        content = 'testing: > 2'

        with self.assertRaises(document_front_matter.BadFormatError):
            document_front_matter.DocumentFrontMatter(
                doc, raw_front_matter=content)

        doc = self.pod.get_doc('/content/pages/html.html')
        content = textwrap.dedent("""
            name: Jane Doe
            ---
            foo: bar
            """).lstrip()
        with self.assertRaises(document_front_matter.BadFormatError):
            document_front_matter.DocumentFrontMatter(
                doc, raw_front_matter=content)

        doc = self.pod.get_doc('/content/pages/html.html')
        content = textwrap.dedent("""
            - alpha
            - beta
            - charlie
            """).lstrip()
        with self.assertRaises(document_front_matter.BadFormatError):
            document_front_matter.DocumentFrontMatter(
                doc, raw_front_matter=content)

    def test_empty_raw_front_matter(self):
        """Test for empty or missing front matter."""
        doc = self.pod.get_doc('/content/pages/html.html')

        document_front_matter.DocumentFrontMatter(
            doc, raw_front_matter=None)

    def test_split_front_matter(self):
        """Test splitting valid front matter from content."""
        # Normal front matter.
        content = textwrap.dedent("""
            ---
            name: Jane Doe
            ---
            Jane was adventuring.
            """)
        expected = ('name: Jane Doe', 'Jane was adventuring.')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter.split_front_matter(content))

        # No front matter, so only content returned.
        content = textwrap.dedent("""
            Jane was adventuring.
            """)
        expected = (None, 'Jane was adventuring.')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter.split_front_matter(content))

        # Empty front matter, so only content returned.
        content = textwrap.dedent("""
            ---
            ---
            Jane was adventuring.
            """)
        expected = (None, 'Jane was adventuring.')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter.split_front_matter(content))

        # Invalid front matter, too many sections.
        content = textwrap.dedent("""
            name: Jane Doe
            ---
            foo: bar
            ---
            Jane was adventuring.
            """)

        with self.assertRaises(document_front_matter.BadFormatError):
            document_front_matter.DocumentFrontMatter.split_front_matter(content)

    def test_export(self):
        """Test exporting the front raw matter."""
        expected = textwrap.dedent("""
            $title@: HTML Page
            $hidden: true
            """).strip()
        doc = self.pod.get_doc('/content/pages/html.html')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter(doc).export())

    def test_inherit(self):
        """Test that local specific front matter inherits from upstream docs."""
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_file('/content/pages/foo@en_us.yaml', textwrap.dedent("""\
            $title: HTML EN-US Page
            foo: three
            foobar:
              foo_3: test 3
            """))
        pod.write_file('/content/pages/foo@en.yaml', textwrap.dedent("""\
            $title: HTML EN Page
            foo: two
            bar: true
            foobar:
              foo_2: test 2
            """))
        pod.write_file('/content/pages/foo.yaml', textwrap.dedent("""\
            $title: HTML Page
            foo: one
            foobar:
              foo_1: test 1
            """))

        doc = pod.get_doc('/content/pages/foo@en_us.yaml')
        front_matter = doc.format.front_matter
        data = front_matter.data
        self.assertEqual('HTML EN-US Page', data['$title'])
        self.assertEqual('three', data['foo'])
        self.assertEqual(True, data['bar'])
        self.assertDictEqual({
            'foo_3': 'test 3',
            'foo_2': 'test 2',
            'foo_1': 'test 1',
        }, data['foobar'])

        doc = pod.get_doc('/content/pages/foo@en.yaml')
        front_matter = doc.format.front_matter
        data = front_matter.data
        self.assertEqual('HTML EN Page', data['$title'])
        self.assertEqual('two', data['foo'])
        self.assertEqual(True, data['bar'])
        self.assertDictEqual({
            'foo_2': 'test 2',
            'foo_1': 'test 1',
        }, data['foobar'])

        doc = pod.get_doc('/content/pages/foo.yaml')
        front_matter = doc.format.front_matter
        data = front_matter.data
        self.assertEqual('HTML Page', data['$title'])
        self.assertEqual('one', data['foo'])
        self.assertDictEqual({
            'foo_1': 'test 1',
        }, data['foobar'])


if __name__ == '__main__':
    unittest.main()
