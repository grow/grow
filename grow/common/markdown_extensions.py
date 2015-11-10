"""
    The Pygments Markdown Preprocessor
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    This fragment is a Markdown_ preprocessor that renders source code
    to HTML via Pygments.  To use it, invoke Markdown like so::

        import markdown
        html = markdown.markdown(someText, extensions=[CodeBlockExtension()])

    This uses CSS classes by default, so use
    ``pygmentize -S <some style> -f html > pygments.css``
    to create a stylesheet to be added to the website.

    You can then highlight source code in your markdown markup::

        [sourcecode:lexer]
        some code
        [/sourcecode]

    .. _Markdown: https://pypi.python.org/pypi/Markdown

    :copyright: Copyright 2006-2014 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from markdown import extensions
from markdown import preprocessors
from pygments import highlight
from pygments import lexers
from pygments.formatters.html import HtmlFormatter
from pygments.lexers import TextLexer
from pygments.lexers import get_lexer_by_name
import re


class IncludePreprocessor(preprocessors.Preprocessor):

  REGEX = re.compile("^\[include\('([^')]*)'\)\]")

  def __init__(self, pod, markdown_instance):
    self.pod = pod
    self.markdown = markdown_instance

  def run(self, lines):
    new_lines = []
    for line in lines:
      pod_paths = IncludePreprocessor.REGEX.findall(line)
      if not pod_paths or line.startswith('    '):
        new_lines.append(line)
      for pod_path in pod_paths:
        doc = self.pod.get_doc(pod_path)
        included_lines = doc.body.split('\n')
        new_lines.extend(included_lines)
    return new_lines


class IncludeExtension(extensions.Extension):

  def __init__(self, pod):
    self.pod = pod

  def extendMarkdown(self, md, md_globals):
    md.registerExtension(self)
    self.processor = IncludePreprocessor(self.pod, md)
    self.processor.md = md
    # Adds the "include" preprocessor to the beginning of the list of preprocessors.
    # https://github.com/waylan/Python-Markdown/blob/master/markdown/odict.py#L7
    md.preprocessors.add('include', self.processor, '_begin')


class UrlPreprocessor(preprocessors.Preprocessor):

  REGEX = re.compile("\[url\('([^')]*)'\)\]")

  def __init__(self, pod, markdown_instance):
    self.pod = pod
    self.markdown = markdown_instance

  def run(self, lines):
    new_lines = []
    for line in lines:
      pod_paths = UrlPreprocessor.REGEX.findall(line)
      if not pod_paths or line.startswith('    '):
        new_lines.append(line)
      else:
        for pod_path in pod_paths:
          doc = self.pod.get_doc(pod_path)
          line = re.sub(UrlPreprocessor.REGEX, doc.url.path, line)
        new_lines.append(line)
    return new_lines


class UrlExtension(extensions.Extension):

  def __init__(self, pod):
    self.pod = pod

  def extendMarkdown(self, md, md_globals):
    md.registerExtension(self)
    self.processor = UrlPreprocessor(self.pod, md)
    self.processor.md = md
    # Adds the "include" preprocessor to the beginning of the list of preprocessors.
    # https://github.com/waylan/Python-Markdown/blob/master/markdown/odict.py#L7
    md.preprocessors.add('url', self.processor, '_begin')


class CodeBlockPreprocessor(preprocessors.Preprocessor):
  pattern = re.compile(r'\[sourcecode:(.+?)\](.+?)\[/sourcecode\]', re.S)
  formatter = HtmlFormatter(noclasses=True)

  def run(self, lines):
    def repl(m):
      try:
        lexer = lexers.get_lexer_by_name(m.group(1))
      except ValueError:
        lexer = lexers.TextLexer()
      code = highlight(m.group(2), lexer, self.formatter)
      return '\n\n<div class="code">%s</div>\n\n' % code
    joined_lines = "\n".join(lines)
    joined_lines = self.pattern.sub(repl, joined_lines)
    return joined_lines.split("\n")


class CodeBlockExtension(extensions.Extension):

  def extendMarkdown(self, md, md_globals):
    md.preprocessors.add('CodeBlockPreprocessor', CodeBlockPreprocessor(), '_begin')
