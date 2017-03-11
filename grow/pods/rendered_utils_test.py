from grow.pods import footnotes
from grow.pods import rendered_utils
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class RenderedUtilitiesTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_footnotes(self):
        doc = self.pod.get_doc('/content/pages/about.yaml')
        rendered_utilities = rendered_utils.RenderedUtilities(doc)
        self.assertIsInstance(rendered_utilities.footnotes, footnotes.Footnotes)


if __name__ == '__main__':
    unittest.main()
