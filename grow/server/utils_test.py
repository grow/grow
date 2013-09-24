from grow.server import utils
import unittest


class UtilsTest(unittest.TestCase):

  def test_get_changeset_from_hostname(self):
    self.assertEqual(
        'foo-bar-123',
        utils.get_changeset('foo-bar-123-dot-example.com'))
    self.assertEqual(
        None,
        utils.get_changeset('foo-baz--123-dot-example.com'))
    self.assertEqual(
        None,
        utils.get_changeset('foo-baz--bar-dot-example.com'))
    self.assertEqual(
        None,
        utils.get_changeset('blah-dot-example.com'))


if __name__ == '__main__':
  unittest.main()
