import unittest
import utils


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


if __name__ == '__main__':
  unittest.main()

