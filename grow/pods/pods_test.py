from grow.pods import errors
from grow.pods import pods
from grow.pods import routes
from grow.pods import storage
import unittest


class PodTest(unittest.TestCase):

  def setUp(self):
    self.pod = pods.Pod('grow/pods/testdata/pod/', storage=storage.FileStorage)

  def test_list_dir(self):
    self.pod.list_dir('/content')

  def test_read_file(self):
    self.pod.read_file('/pod.yaml')

  def test_write_file(self):
    self.pod.write_file('/dummy.yaml', 'foo')

  def test_list_blueprints(self):
    self.pod.list_blueprints()

  def test_match(self):
    controller = self.pod.match('/')
    controller = self.pod.match('/en/about')
    self.assertRaises(routes.Errors.NotFound, self.pod.match, '/dummy')

  def test_export(self):
    self.pod.export()

  def test_dump(self):
    self.pod.dump()

  def test_to_message(self):
    self.pod.to_message()


if __name__ == '__main__':
  unittest.main()
