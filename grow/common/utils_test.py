from grow.testing import testing
from . import utils
import unittest


class UtilsTestCase(unittest.TestCase):

  def test_walk(self):
    data = {
      'foo': 'bar',
      'bam': {
        'foo': 'bar2',
        'foo2': ['bar3', 'bar4'],
      }
    }

    actual = []
    callback = lambda item, key, node: actual.append(item)
    utils.walk(data, callback)

    expected = ['bar', 'bar2', 'bar3', 'bar4']
    self.assertItemsEqual(expected, actual)

  def test_parse_yaml(self):
    pod = testing.create_test_pod()
    content = pod.read_file('/data/constructors.yaml')
    result = utils.parse_yaml(content, pod=pod)
    doc = pod.get_doc('/content/pages/home.yaml')
    self.assertEqual(doc, result['doc'])
    for item in result['docs']:
      self.assertEqual(doc, item)


if __name__ == '__main__':
  unittest.main()
