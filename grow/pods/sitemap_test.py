from . import sitemap
from grow.pods import pods
from grow import storage
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
        content = controller.render(params)
        letters = sorted(letters)
        indices = [content.find(letter) for letter in letters]
        self.assertNotIn(-1, indices)
        self.assertListEqual(indices, sorted(indices))

    def test_custom_sitemap_template(self):
        pod = testing.create_pod()
        pod.write_yaml('/podspec.yaml', {
            'sitemap': {
                'enabled': True,
                'template': '/views/sitemap.xml',
            },
        })
        pod.write_file('/views/sitemap.xml', 'foo')
        pod.write_yaml('/content/pages/_blueprint.yaml', {
            '$path': '/{base}/',
            '$view': '/views/base.html',
        })
        pod.write_yaml('/content/pages/foo.yaml', {
            '$title': 'Foo',
        })
        pod.write_file('/views/base.html', '{{doc.html}}')
        paths_to_contents = {}
        for rendered_doc in pod.export():
            paths_to_contents[rendered_doc.path] = rendered_doc.read()
        content = paths_to_contents['/sitemap.xml']
        self.assertEqual(content, 'foo')


if __name__ == '__main__':
    unittest.main()
