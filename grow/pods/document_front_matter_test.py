import unittest

from . import document_front_matter
from . import pods
from . import storage
from grow.testing import testing
import textwrap


class DocumentFrontmatterTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_split_front_matter(self):
        # Normal front matter.
        input = textwrap.dedent("""
            ---
            name: Jane Doe
            ---
            Jane was adventuring.
            """)
        expected = ('name: Jane Doe', 'Jane was adventuring.')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter.split_front_matter(input))

        # No front matter, so only content returned.
        input = textwrap.dedent("""
            Jane was adventuring.
            """)
        expected = (None, 'Jane was adventuring.')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter.split_front_matter(input))

        # Empty front matter, so only content returned.
        input = textwrap.dedent("""
            ---
            ---
            Jane was adventuring.
            """)
        expected = (None, 'Jane was adventuring.')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter.split_front_matter(input))

        # Invalid front matter, missing opening dashes.
        input = textwrap.dedent("""
            name: Jane Doe
            ---
            Jane was adventuring.
            """)
        expected = (None, 'name: Jane Doe\n---\nJane was adventuring.')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter.split_front_matter(input))

    def test_export(self):
        expected = textwrap.dedent("""
            $title@: HTML Page
            $hidden: true
            """).strip()
        doc = self.pod.get_doc('/content/pages/html.html')

        self.assertEquals(
            expected,
            document_front_matter.DocumentFrontMatter(doc).export())

    def test_inherit(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {})
        pod.write_file('/content/pages/foo@en-us.yaml', textwrap.dedent("""\
            $title: HTML EN-US Page
            foo: three
            """))
        pod.write_file('/content/pages/foo@en.yaml', textwrap.dedent("""\
            $title: HTML EN Page
            foo: two
            bar: true
            """))
        pod.write_file('/content/pages/foo.yaml', textwrap.dedent("""\
            $title: HTML Page
            foo: one
            """))

        doc = pod.get_doc('/content/pages/foo@en-us.yaml')
        front_matter = doc.format.front_matter
        data = front_matter.data
        self.assertEqual('HTML EN-US Page', data['$title'])
        self.assertEqual('three', data['foo'])
        self.assertEqual(True, data['bar'])

        doc = pod.get_doc('/content/pages/foo@en.yaml')
        front_matter = doc.format.front_matter
        data = front_matter.data
        self.assertEqual('HTML EN Page', data['$title'])
        self.assertEqual('two', data['foo'])
        self.assertEqual(True, data['bar'])

        doc = pod.get_doc('/content/pages/foo.yaml')
        front_matter = doc.format.front_matter
        data = front_matter.data
        self.assertEqual('HTML Page', data['$title'])
        self.assertEqual('one', data['foo'])


if __name__ == '__main__':
    unittest.main()
