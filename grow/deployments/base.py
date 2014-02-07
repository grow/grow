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
  (4) An index is generated locally, and the local index is compared to the
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

  __init__(self, *args, **kwargs)
    You may override the __init__ method to take arguments needed by your
    deployment. For example, if deploying to a cloud storage provider, you
    may init the deployment with access keys.

  delete_file(self, path)
    Deletes a file at the destination, given the file's pod path.

  postlaunch(self)
    Performs any post-launch tasks.

  prelaunch(self)
    Performs any pre-launch configuration/tasks.

  read_file(self, path)
    Reads a file at the destination, returning the file's content.

  write_file(self, path, content)
    Writes a file at the destination, given the file's pod path and its content.

Once you've written a new deployment, add it to this directory's __init__.py.

To make the deployment available from the command line "grow deploy" utility,
you must modify the DeployCmd class in pygrow/grow/commands.py.
"""

import logging
from grow.pods import index


class Error(Exception):
  pass


class NotFoundError(Error, IOError):
  pass


class BaseDeployment(object):

  def __init__(self, *args, **kwargs):
    pass

  def get_index_at_destination(self):
    path = index.Index.BASENAME
    try:
      content = self.read_file(path)
      logging.info('Loaded index destination.')
      return index.Index.from_yaml(content)
    except NotFoundError:
      logging.info('No index found at destination, assuming new deployment.')
      return index.Index()

  def read_file(self, path):
    raise NotImplementedError

  def write_file(self, path, content):
    raise NotImplementedError

  def deploy(self, pod, dry_run=False):
    raise NotImplementedError

  def postlaunch(self):
    raise NotImplementedError

  def prelaunch(self):
    raise NotImplementedError
