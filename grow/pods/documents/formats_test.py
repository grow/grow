from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class FormatsTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_markdown(self):
        doc = self.pod.get_doc('/content/pages/intro.md')
        self.assertEqual('<p>About page.</p>', doc.html)
        self.assertEqual('About page.', doc.body)

    def test_locales(self):
        path = '/content/localized/multiple-locales.yaml'
        doc = self.pod.get_doc(path)
        self.assertEqual('base', doc.foo)
        de_doc = self.pod.get_doc(path, locale='de')
        self.assertEqual('de', de_doc.foo)
        it_doc = self.pod.get_doc(path, locale='it')
        self.assertEqual('it_fr', it_doc.foo)
        fr_doc = self.pod.get_doc(path, locale='fr')
        self.assertEqual('it_fr', fr_doc.foo)

    def test_yaml(self):
        doc = self.pod.get_doc('/content/pages/home.yaml')
        self.assertEqual('bar', doc.fields['foo'])

        doc = self.pod.get_doc('/content/pages/about.yaml')
        self.assertEqual('bar', doc.foo)
        doc = self.pod.get_doc('/content/pages/about.yaml', locale='de')
        body = (
            '$locale: de\n'
            '$title@: AboutDE\n'
            'foo: baz'
        )
        self.assertEqual(body, doc.body)
        self.assertEqual('baz', doc.foo)

    def test_html(self):
        doc = self.pod.get_doc('/content/pages/html.html')
        self.assertEqual('HTML Page', doc.title)
        self.assertEqual('<div>HTML Content.</div>', doc.body)
        content = (
            '---\n'
            '$title@: HTML Page\n'
            '$hidden: true\n'
            '---\n'
            '<div>HTML Content.</div>\n'
        )
        self.assertEqual(content, doc.content)


if __name__ == '__main__':
    unittest.main()
