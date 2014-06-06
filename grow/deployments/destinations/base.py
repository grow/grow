"""A base class for a deployment.

A deployment takes a pod, builds a static fileset from it, and deploys it to a
remote location, suitable for serving the web site to live end users.
Currently, Grow only supports static deployments, however, this may change as
Grow implements requirements such as "password protection" and geolocation.

The deployment process generally works like this:

  (1) A pod is exported, creating a dictionary mapping file paths to content.
  (2) A connection is made between Grow and the destination.
  (3) An index is retrieved from the destination, which contains a mapping
      of file paths to a sha-1 hash value of the file's content.
  (4) An  indexis generated locally, and the local index is compared to the
      index at the destination. This allows Grow to produce a diff between
      the local ("canary") fileset and the destination's fileset.
  (5) An integration test (if any) is performed.
  (6) If the deployment is a dry run, the process ends here.
  (7) Any required pre-launch configuration to the destination is applied.
  (8) The diff between the canary fileset and the destination fileset is
      applied.
  (9) An updated index is written to the destination.
  (10) Any required post-launch configuration to the destination is applied.
       The deployment is complete.

All deployments follow this process, and the BaseDeployment class takes
care of most of the hard work and business logic. So if you're adding a new
deployment, you'll just have to implement the following methods:

  delete_file(self, path)
    Deletes a file at the destination, given the file's pod path.

  get_destination_address(self):
    Returns the address of the destination (used to show the user where
    the pod has been deployed to).

  read_file(self, path)
    Reads a file at the destination, returning the file's content.

  write_file(self, path, content)
    Writes a file at the destination, given the file's pod path and its content.

The following methods are optional to implement:

  __init__(self, **kwargs)
    Sets any parameters required by the other subclassed methods.

  postlaunch(self, dry_run)
    Performs any post-launch tasks.

  prelaunch(self, dry_run)
    Performs any pre-launch configuration/tasks.

  write_index_at_destination(self, new_index):
    Writes the index of the newly-built pod to the destination.

Once you've written a new deployment, add it to this directory's __init__.py.

To make the deployment available from the command line "grow deploy" utility,
you must modify the DeployCmd class in pygrow/grow/commands.py.
"""

from . import messages
from .. import tests
from ..indexes import indexes
from grow.common import utils
import inspect
import logging
import os
import time


class Error(Exception):
  pass


class NotFoundError(Error, IOError):
  pass


class DeploymentTestCase(object):

  def __init__(self, deployment):
    self.deployment = deployment

  def test_write_file(self):
    message = messages.TestResultMessage(title='Write a file')
    path = os.path.join(self.deployment.get_temp_dir(), 'test.txt')
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
  threaded = True
  TestCase = DeploymentTestCase

  def __init__(self, config):
    self.config = config

  def read_file(self, path):
    """Returns a file-like object."""
    raise NotImplementedError

  def write_file(self, path, content):
    raise NotImplementedError

  def get_destination_address(self):
    raise NotImplementedError

  def test(self):
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

  def write_index_at_destination(self, new_index):
    path = self.get_index_path()
    content = indexes.Index.to_string(new_index)
    self.write_file(path, content)
    logging.info('Wrote index: {}'.format(path))

  def get_temp_dir(self):
    return '/.grow/tmp/'

  def get_index_path(self):
    return '/.grow/index.json'

  def get_index_at_destination(self):
    try:
      content = self.read_file(self.get_index_path())
      return indexes.Index.from_string(content)
    except IOError:
      logging.info('No index found at destination, assuming new deployment.')
      return indexes.Index.create()

  def postlaunch(self, dry_run=False):
    pass

  def prelaunch(self, dry_run=False):
    pass

  def deploy(self, paths_to_contents, repo=None, dry_run=False, confirm=False):
    destination_address = self.get_destination_address()
    logging.info('Deploying to: {}'.format(destination_address))
    self._prelaunch()
    self.prelaunch(dry_run=dry_run)

    try:
      deployed_index = self.get_index_at_destination()
      new_index = indexes.Index.create(paths_to_contents)
      if repo:
        indexes.Index.add_repo(new_index, repo)
      diff = indexes.Diff.create(new_index, deployed_index)
      if indexes.Diff.is_empty(diff):
        text = utils.colorize('{white}Diff is empty, nothing to launch, aborted.{/white}')
        logging.info(text)
        return
      if dry_run:
        return
      if confirm:
        indexes.Diff.pretty_print(diff)
        logging.info('About to launch => {}'.format(destination_address))
        if not utils.interactive_confirm('Proceed?'):
          logging.info('Launch aborted.')
          return

      self.start_time = time.time()
      indexes.Diff.apply(
          diff, paths_to_contents, write_func=self.write_file,
          delete_func=self.delete_file, threaded=self.threaded)
      # TODO(jeremydw): Index should only be updated if the diff was entirely
      # successfully applied.
      self.write_index_at_destination(new_index)
    finally:
      self.postlaunch()
      self._postlaunch()

    return diff

  def _prelaunch(self):
    self.test()

  def _postlaunch(self):
    if hasattr(self, 'start_time'):
      logging.info('Deployed to: {}'.format(self.get_destination_address()))
      logging.info('Done in {}s!'.format(time.time() - self.start_time))
