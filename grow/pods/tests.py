from grow.common import utils

# TODO(jeremydw): This is just a proof of concept. We probably shouldn't invent our
# own testing system, but rather leverage some other existing one. It might be a
# "happy medium" to store test configurations in a pod's /tests.yaml file, but
# use a third party test runner.


class Error(Exception):
  pass


class TestFailedError(Error, AssertionError):
  pass


class Tests(object):

  def __init__(self, pod):
    self.pod = pod

  @property
  @utils.memoize
  def yaml(self):
    return utils.parse_yaml(self.pod.read_file('/tests.yaml'))[0]

  @property
  def exists(self):
    return False

  def run(self):
    for test in self.yaml['tests']:
      routes = self.pod.get_routes()
      controller = routes.match(test['path'])
      html = controller.render()
      if 'assertInHtml' not in test:
        continue
      for value in test['assertInHtml']:
        if value not in html:
          message = '"{} not in HTML of rendered route: {}'.format(value, controller)
          raise TestFailedError(message)
