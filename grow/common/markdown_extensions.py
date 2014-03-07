import re
from markdown import extensions
from markdown import preprocessors


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
