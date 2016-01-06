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


if __name__ == '__main__':
    unittest.main()
