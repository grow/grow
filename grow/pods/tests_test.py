from grow.pods import pods
from grow.pods import storage
import unittest


class RoutesTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/',
                        storage=storage.FileStorage)

  def test_run(self):
    self.pod.tests.run()


if __name__ == '__main__':
  unittest.main()

