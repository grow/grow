"""Test the pod partial."""

import unittest
from grow import storage
from grow.pods import pods
from grow.testing import testing


class PartialTestCase(unittest.TestCase):
    """Tests for partials."""

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)


if __name__ == '__main__':
    unittest.main()
