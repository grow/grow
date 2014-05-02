from grow.pods import pods
from grow.pods import storage
from grow.stats import stats
import os
import unittest

TESTDATA_DIR = os.path.join(os.path.dirname(__file__), 'testdata', 'pod')


class StatsTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_to_message(self):
    stat = stats.Stats(self.pod)
    stat.to_message()


if __name__ == '__main__':
  unittest.main()
