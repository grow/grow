"""Tests for SDK Updater."""

import unittest
from grow.pods import pods
from grow.pods import storage
from grow.sdk import updater
from grow.testing import testing


class UpdaterTestCase(unittest.TestCase):
    """Test the SDK Updater."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)
        self.updater = updater.Updater(self.pod)

    def test_something(self):
        """?"""
        pass
