from . import security


_test_cases = [
    security.SecurityTestCase,
]


class Error(Exception):
  pass


class Tests(object):

  def __init__(self, pod):
    self.pod = pod

  def run(self):
    paths_to_contents = self.pod.export()
    for test_case in _test_cases:
      case = test_case(self.pod, paths_to_contents)
      case.run()
