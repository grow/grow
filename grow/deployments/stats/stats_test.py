from . import stats
from grow.pods import pods
from grow.pods import storage
from grow.testing import testing
import unittest


class StatsTest(unittest.TestCase):

    def setUp(self):
        dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(dir_path, storage=storage.FileStorage)

    def test_to_message(self):
        stat = stats.Stats(self.pod)
        stat.to_message()
        stat.to_string()


if __name__ == '__main__':
    unittest.main()
