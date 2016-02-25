from . import urls
from grow.pods import pods
from grow.testing import testing
import os
import unittest


class UrlTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path)

    def test_relative_path(self):
        pod_path = '/content/pages/about.yaml'
        relative_to = self.pod.get_doc(pod_path).url.path
        url = urls.Url('/foo/bar/baz/', relative_to=relative_to)
        self.assertEqual('../foo/bar/baz/', url.relative_path)
        relative_to = self.pod.get_doc(pod_path, locale='de').url.path
        url = urls.Url('/foo/bar/baz/', relative_to=relative_to)
        self.assertEqual('../../foo/bar/baz/', url.relative_path)


if __name__ == '__main__':
    unittest.main()
