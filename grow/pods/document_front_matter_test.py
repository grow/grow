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
        self.doc = pods.Pod(dir_path, storage=storage.FileStorage)

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


if __name__ == '__main__':
    unittest.main()
