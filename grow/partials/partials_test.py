"""Test the pod partials."""

import unittest
from grow import storage
from grow.pods import pods
from grow.testing import testing


class PartialsTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_get_partials(self):
        """Test that partials are found correctly."""
        partials = self.pod.partials
        expected = ['hero']
        self.assertListEqual(expected, [partial.key for partial in partials.get_partials()])


if __name__ == '__main__':
    unittest.main()
