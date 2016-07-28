from . import sitemap
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class SitemapTest(unittest.TestCase):

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_render(self):
        controller = sitemap.SitemapController(pod=self.pod)
        controller.render()

    def test_sitemap_enabled(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'sitemap': {
                'enabled': True,
            },
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
        })
        pod.write_yaml('/content/pages/foo.yaml', {
            '$title': 'Foo',
        })
        pod.write_yaml('/content/pages/bar.yaml', {
            '$title': 'Bar',
            '$sitemap': {
                'enabled': False,
            },
        })
        controller, params = pod.match('/sitemap.xml')
        content = controller.render(params)
        # Verify $sitemap:enabled = false.
        self.assertIn('/foo/', content)
        self.assertNotIn('/bar/', content)

    def test_sitemap_sorted(self):
        letters = ('alpha', 'beta', 'gamma', 'delta', 'epsilon', 'zeta')
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'sitemap': {
                'enabled': True,
            },
        })
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
        })
        for letter in letters:
            pod.write_yaml('/content/pages/{0}.yaml'.format(letter), {
                '$title': letter,
            })
        controller, params = pod.match('/sitemap.xml')
        docs = controller._list_docs()
        for letter, doc in zip(sorted(letters), docs):
            self.assertIn(letter, doc.url.path)



if __name__ == '__main__':
    unittest.main()
