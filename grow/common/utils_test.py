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
    callback = lambda item, _: actual.append(item)
    utils.walk(data, callback)

    expected = ['bar', 'bar2', 'bar3', 'bar4']
    self.assertItemsEqual(expected, actual)

  def test_parse_markdown(self):
    content = (
        '---\n'
        'foo: bar\n'
        '---\n'
        '# Bam\n'
    )
    fields, content = utils.parse_markdown(content)
    self.assertEqual({'foo': 'bar'}, fields)
    self.assertEqual('# Bam', content)

    content = (
        '---\n'
        'foo: bar\n'
        '---\n'
    )
    fields, content = utils.parse_markdown(content)
    self.assertEqual({'foo': 'bar'}, fields)
    self.assertEqual('', content)

    content = (
        '# Bam'
    )
    fields, content = utils.parse_markdown(content)
    self.assertEqual(None, fields)
    self.assertEqual('# Bam', content)

    localized_content = (
        '---\n'
        'locale: foo\n'
        '---\n'
        '# Foo\n'
        '---\n'
        'locale: bar\n'
        '---\n'
        '# Bar\n'
        '---\n'
        'locale: qaz\n'
        '---\n'
        '# Qaz\n'
    )


if __name__ == '__main__':
  unittest.main()

