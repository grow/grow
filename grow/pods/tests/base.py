import inspect
import re
from . import messages


class PodTestCase(object):

  _regex_tests = None

  def __init__(self, pod, paths_to_contents):
    self.pod = pod
    self.paths_to_contents = paths_to_contents

  def __iter__(self):
    for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
      if name.startswith('test'):
        yield func

  def run(self):
    for func in self:
      result = func()
      for fail in result.fails:
        print '{}:{}  {}'.format(fail.path, fail.snippet.line_num, fail.text)
      for warning in result.warnings:
        print '{}:{}  {}'.format(warning.path, warning.snippet.line_num, warning.text)
    print 'All done.'


class RegExTestCase(PodTestCase):

  def test(self):
    results = messages.TestResultsMessage()
    for path, content in self.paths_to_contents.iteritems():
      for i, line in enumerate(content.split('\n')):
        for check in self.checks:
          if re.search(check.regex, line):
            result = messages.TestResultMessage()
            result.path = path
            result.status = check.status
            result.text = check.text
            result.snippet = messages.SnippetMessage(line_num=i, lines=[line])
            if result.status == messages.Status.WARN:
              results.warnings.append(result)
            elif result.status == messages.Status.FAIL:
              results.fails.append(result)
    return results
