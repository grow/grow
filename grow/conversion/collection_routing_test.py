"""Tests for converting a pod to use collection level routing."""

import unittest
from grow import storage
from grow.pods import pods
from grow.conversion import collection_routing
from grow.testing import testing


class ConversionDocumentTestCase(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)
        self.pod.write_yaml('/podspec.yaml', {})

    def test_something(self):
        """Testing?"""
        pass
