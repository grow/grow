"""Tests for document fields."""

import textwrap
import unittest
from grow.documents import document_format
from grow.pods import pods
from grow import storage
from grow.testing import testing


class DocumentFormatTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_content(self):
        doc = self.pod.get_doc('/content/pages/html.html')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        expected = textwrap.dedent('<div>HTML Content.</div>')
        self.assertEquals(expected, doc_format.content)

    def test_from_doc(self):
        doc = self.pod.get_doc('/content/pages/html.html')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        self.assertIsInstance(doc_format, document_format.HtmlDocumentFormat)

        doc = self.pod.get_doc('/content/pages/intro.md')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        self.assertIsInstance(
            doc_format, document_format.MarkdownDocumentFormat)

        doc = self.pod.get_doc('/content/pages/home.yaml')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        self.assertIsInstance(
            doc_format, document_format.YamlDocumentFormat)

        doc = self.pod.get_doc('/content/pages/text.txt')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        self.assertIsInstance(
            doc_format, document_format.TextDocumentFormat)

        with self.assertRaises(document_format.BadFormatError):
            document_format.DocumentFormat.from_doc()

    def test_front_matter(self):
        doc = self.pod.get_doc('/content/pages/html.html')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        expected = textwrap.dedent("""
        $title@: HTML Page
        $hidden: true
        """)
        self.assertEquals(expected.strip(), doc_format.front_matter.export())

    def test_raw_content(self):
        doc = self.pod.get_doc('/content/pages/html.html')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        expected = textwrap.dedent("""
        ---
        $title@: HTML Page
        $hidden: true
        ---
        <div>HTML Content.</div>
        """)
        self.assertEquals(expected.strip(), doc_format.raw_content.strip())

    def test_to_raw_content(self):
        doc = self.pod.get_doc('/content/pages/html.html')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        expected = textwrap.dedent("""
        ---
        $title@: HTML Page
        $hidden: true
        ---
        <div>HTML Content.</div>
        """)
        self.assertEquals(expected.strip(), doc_format.to_raw_content().strip())

        doc = self.pod.get_doc('/content/empty-front-matter/empty-front-matter.html')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        expected = textwrap.dedent("""
        <div>Empty front matter.</div>
        """)
        self.assertEquals(expected.strip(), doc_format.to_raw_content().strip())

        doc = self.pod.get_doc('/content/pages/root.yaml')
        doc_format = document_format.DocumentFormat.from_doc(doc=doc)
        expected = textwrap.dedent("""
        $path: "{root}/base/"
        $view: /views/home.html
        $localization:
          locales:
        """)
        self.assertEquals(expected.strip(), doc_format.to_raw_content().strip())


if __name__ == '__main__':
    unittest.main()
