"""Tests for Themes."""

import unittest
from grow.pods import pods
from grow import storage
from grow.sdk import themes
from grow.testing import testing


class ThemesTestCase(unittest.TestCase):
    """Test the Themes."""

    def setUp(self):
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_something(self):
        """Test ?."""
        pass
