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

    content = (
        '---\n'
        '$locale: foo\n'
        '---\n'
        '# Foo\n'
        '---\n'
        '$locale: bar\n'
        '---\n'
        '# Bar\n'
        '---\n'
        '$locale: qaz\n'
        '---\n'
        '# Qaz\n'
    )
    fields, content = utils.parse_markdown(content, locale='bar')
    self.assertEqual('# Bar', content)

    content = (
        '---\n'
        '$locale: a\n'
        'main: a\n'
        'foo: bar\n'
        '---\n'
        '$locale: b\n'
        'foo: baz\n'
        '---\n'
        '$locale: c\n'
        'foo: qux\n'
    )
    fields = utils.parse_yaml(content, locale='a')
    self.assertEqual({'foo': 'bar', '$locale': 'a', 'main': 'a'}, fields)
    fields = utils.parse_yaml(content, locale='b')
    self.assertEqual({'foo': 'baz', '$locale': 'b'}, fields)
    fields = utils.parse_yaml(content, locale='b', default_locale='a')
    self.assertEqual({'foo': 'baz', 'main': 'a', '$locale': 'b'}, fields)


if __name__ == '__main__':
  unittest.main()

