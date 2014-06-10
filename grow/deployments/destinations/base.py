"""A base class for a deployment.

A deployment takes a pod, builds a static fileset from it, and deploys it to a
remote location, suitable for serving the web site to live end users.
Currently, Grow only supports static deployments, however, this may change as
Grow implements features such as "password protection" and geolocation.

The deployment process generally works like this:

  (1) A pod is exported, creating a dictionary mapping file paths to content.
  (2) A connection is made between Grow and the destination.
  (3) Control files are retrieved from the destination, if they exist. All
      control files are serialized ProtoRPC messages. The most important
      control file is "index.proto.json", which contains an index of file
      paths to sha-1 hashes of each file's content.
  (4) An index is generated locally, and the local index is compared to the
      index at the destination. This allows Grow to produce a diff between
      the local ("canary") fileset and the destination's fileset.
  (5) An integration test (if any) is performed.
  (6) If the deployment is a dry run, the process ends here.
  (7) Any required pre-launch configuration to the destination is applied.
  (8) The diff between the local and remote fileset is applied.
  (9) Updated control files are written to the desination.
  (10) Any required post-launch configuration to the destination is applied.

  The deployment is complete!

All deployments follow this process, and the BaseDeployment class takes
care of most of the hard work and business logic. So if you're adding a new
deployment, you'll just have to implement the following methods/properties:

  delete_file(self, path)
    Deletes a file at the destination, given the file's pod path.

  read_file(self, path)
    Reads a file at the destination, returning the file's content.

  write_file(self, path, content)
    Writes a file at the destination, given the file's pod path and its content.

  NAME
    A string identifying the deployment.

The following methods are optional to implement:

  postlaunch(self, dry_run)
    Performs any post-launch tasks.

  prelaunch(self, dry_run)
    Performs any pre-launch configuration/tasks.

  write_control_file(self, basename, content):
    Writes a control file to the destination.

If your deployment requires configuration, you should add a nested class:

  Config
    A ProtoRPC message for deployment configuration.

New builtin deployments should be added to the list of builtins in
grow/deployments/deployments.py. Proprietary deployments can be registered
using deployments.register_deployment.
"""

from . import messages
from .. import tests
from ..indexes import indexes
from grow.common import utils
from xtermcolor import colorize
import inspect
import logging
import os


class Error(Exception):
  pass


class DeploymentTestCase(object):

  def __init__(self, deployment):
    self.deployment = deployment

  def test_write_file(self):
    path = os.path.join(self.deployment.control_dir, 'test.tmp')
    title = 'Can write files to {}'.format(self.deployment)
    message = messages.TestResultMessage(title=title)
    self.deployment.write_file(path, 'test')
    content = self.deployment.read_file(path)
    if content != 'test':
      message.result = messages.Result.FAIL
    self.deployment.delete_file(path)
    return message

  def __iter__(self):
    for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
      if name.startswith('test_'):
        yield func


class BaseDeployment(object):
  TestCase = DeploymentTestCase
  control_dir = '/.grow/'
  index_basename = 'index.proto.json'
  stats_basename = 'stats.proto.json'
  threaded = True

  def __init__(self, config, run_tests=True):
    self.config = config
    self.run_tests = run_tests

  def __str__(self):
    return self.__class__.__name__

  def _get_remote_index(self):
    try:
      content = self.read_control_file(self.index_basename)
      return indexes.Index.from_string(content)
    except IOError:
      return indexes.Index.create()

  def _prelaunch(self, dry_run=False):
    self.prelaunch(dry_run=dry_run)
    if self.run_tests:
      self.test()

  def read_file(self, path):
    """Returns a file-like object."""
    raise NotImplementedError

  def write_file(self, path, content):
    raise NotImplementedError

  def delete_file(self, path):
    raise NotImplementedError

  def delete_control_file(self, path):
    path = os.path.join(self.control_dir, path.lstrip('/'))
    return self.delete_file(path)

  def read_control_file(self, path):
    path = os.path.join(self.control_dir, path.lstrip('/'))
    return self.read_file(path)

  def write_control_file(self, path, content):
    path = os.path.join(self.control_dir, path.lstrip('/'))
    return self.write_file(path, content)

  def test(self):
    logging.info('Running tests...')
    results = messages.TestResultsMessage(test_results=[])
    failures = []
    test_case = self.TestCase(self)
    for func in test_case:
      result_message = func()
      results.test_results.append(result_message)
      if result_message.result != messages.Result.PASS:
        failures.append(result_message)
    if failures:
      raise Exception('{} tests failed.'.format(len(failures)))
    tests.print_results(results)
    return results

  def postlaunch(self, dry_run=False):
    pass

  def prelaunch(self, dry_run=False):
    pass

  def deploy(self, paths_to_contents, stats=None, repo=None, dry_run=False, confirm=False):
    self._prelaunch(dry_run=dry_run)

    try:
      deployed_index = self._get_remote_index()
      new_index = indexes.Index.create(paths_to_contents)
      if repo:
        indexes.Index.add_repo(new_index, repo)
      diff = indexes.Diff.create(new_index, deployed_index)
      if indexes.Diff.is_empty(diff):
        text = 'Diff is empty, nothing to launch, aborted.'
        print colorize(text, ansi=57)
        return
      if dry_run:
        return
      if confirm:
        indexes.Diff.pretty_print(diff)
        text = 'Proceed to launch? => {}'.format(self)
        if not utils.interactive_confirm(text):
          logging.info('Launch aborted.')
          return

      self.prelaunch(dry_run=dry_run)
      indexes.Diff.apply(
          diff, paths_to_contents, write_func=self.write_file,
          delete_func=self.delete_file, threaded=self.threaded)

      self.write_control_file(self.index_basename, indexes.Index.to_string(new_index))
      if stats is not None:
        self.write_control_file(self.stats_basename, stats.to_string())
      else:
        self.delete_control_file(self.stats_basename)

    finally:
      self.postlaunch()

    return diff
