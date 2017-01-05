"""Base class for destinations.

A destination is a place where Grow static builds can be deployed. Grow takes
a pod, builds a static fileset, and deploys it to a remote location (the
desitnation), suitable for serving the web site to live end users.

A "deployment" is a destination loaded up with a configuration.

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

All deployments follow this process, and the BaseDestination class takes
care of most of the hard work and business logic. So if you're adding a new
destination, you'll just have to implement the following methods/properties:

  delete_file(self, path)
    Deletes a file at the destination, given the file's pod path.

  read_file(self, path)
    Reads a file at the destination, returning the file's content.

  write_file(self, path, content)
    Writes a file at the destination, given the file's pod path and its content.

  KIND
    A string identifying the deployment.

The following methods are optional to implement:

  postlaunch(self, dry_run)
    Performs any post-launch tasks.

  prelaunch(self, dry_run)
    Performs any pre-launch configuration/tasks.

  write_control_file(self, basename, content):
    Writes a control file to the destination.

If your destination requires configuration, you should add a nested class:

  Config
    A ProtoRPC message for destination configuration.

New builtin destinations should be added to the list of builtins in
grow/deployments/deployments.py. Proprietary destinations can be registered
using deployments.register_destination.
"""

from . import messages
from .. import indexes
from .. import tests
from grow.common import utils
from grow.pods import env
import inspect
import io
import logging
import os
import subprocess
import sys


class Error(Exception):
    pass


class CommandError(Error):
    pass


class DestinationTestCase(object):

    def __init__(self, deployment):
        self.deployment = deployment

    def test_write_file(self):
        basename = 'test.tmp'
        title = 'Can write files to {}'.format(self.deployment)
        message = messages.TestResultMessage(title=title)
        self.deployment.write_control_file(basename, 'test')
        content = self.deployment.read_control_file(basename)
        if content != 'test':
            message.result = messages.Result.FAIL
        self.deployment.delete_control_file(basename)
        return message

    def __iter__(self):
        for name, func in inspect.getmembers(self, predicate=inspect.ismethod):
            if name.startswith('test_'):
                yield func


class BaseDestination(object):
    TestCase = DestinationTestCase
    diff_basename = 'diff.proto.json'
    index_basename = 'index.proto.json'
    stats_basename = 'stats.proto.json'
    threaded = True
    batch_writes = False
    _control_dir = '/.grow/'
    success = False

    def __init__(self, config, name='default'):
        self.config = config
        self.name = name
        self.pod = None
        self._diff = None
        self._confirm = None

    def __str__(self):
        return self.__class__.__name__

    @property
    def control_dir(self):
        if self.config.keep_control_dir:
            control_dir = self._control_dir
            return os.path.join(self.pod.root, control_dir, 'deployments', self.name)
        if self._has_custom_control_dir:
            return self.config.control_dir
        return self._control_dir

    def _get_remote_index(self):
        try:
            content = self.read_control_file(self.index_basename)
            return indexes.Index.from_string(content)
        except IOError:
            return indexes.Index.create()

    def get_env(self):
        """Returns an environment object based on the config."""
        if self.config.env:
            return env.Env(self.config.env)
        config = env.EnvConfig(host='localhost')
        return env.Env(config)

    def read_file(self, path):
        """Returns a file-like object."""
        raise NotImplementedError

    def write_file(self, path, content):
        raise NotImplementedError

    def delete_file(self, path):
        raise NotImplementedError

    @property
    def _has_custom_control_dir(self):
        return (hasattr(self.config, 'control_dir')
                and self.config.control_dir is not None)

    def delete_control_file(self, path):
        path = os.path.join(self.control_dir, path.lstrip('/'))
        if self.config.keep_control_dir:
            return self.pod.delete_file(path)
        if self._has_custom_control_dir:
            return self.storage.delete(path)
        return self.delete_file(path)

    def read_control_file(self, path):
        path = os.path.join(self.control_dir, path.lstrip('/'))
        if self.config.keep_control_dir:
            return self.pod.read_file(path)
        if self._has_custom_control_dir:
            return self.storage.read(path)
        return self.read_file(path)

    def write_control_file(self, path, content):
        path = os.path.join(self.control_dir, path.lstrip('/'))
        if self.config.keep_control_dir:
            return self.pod.write_file(path, content)
        if self._has_custom_control_dir:
            return self.storage.write(path, content)
        if self.batch_writes:
            return self.write_file({path: content})
        return self.write_file(path, content)

    def test(self):
        results = messages.TestResultsMessage(test_results=[])
        failures = []
        test_case = self.TestCase(self)
        for func in test_case:
            result_message = func()
            results.test_results.append(result_message)
            if result_message.result == messages.Result.FAIL:
                failures.append(result_message)
        tests.print_results(results)
        return results

    def postlaunch(self, dry_run=False):
        pass

    def prelaunch(self, dry_run=False):
        pass

    def login(self, account, reauth=False):
        pass

    def dump(self, pod):
        pod.env = self.get_env()
        return pod.dump()

    def deploy(self, paths_to_contents, stats=None,
               repo=None, dry_run=False, confirm=False, test=True):
        self._confirm = confirm
        self.prelaunch(dry_run=dry_run)
        if test:
            self.test()
        try:
            deployed_index = self._get_remote_index()
            new_index = indexes.Index.create(paths_to_contents)
            if repo:
                indexes.Index.add_repo(new_index, repo)
            diff = indexes.Diff.create(new_index, deployed_index, repo=repo)
            self._diff = diff
            if indexes.Diff.is_empty(diff):
                logging.info('Finished with no diffs since the last build.')
                return
            if dry_run:
                return
            indexes.Diff.pretty_print(diff)
            if confirm:
                text = 'Proceed to deploy? -> {}'.format(self)
                if not utils.interactive_confirm(text):
                    logging.info('Aborted.')
                    return
            indexes.Diff.apply(
                diff, paths_to_contents, write_func=self.write_file,
                delete_func=self.delete_file, threaded=self.threaded,
                batch_writes=self.batch_writes)
            self.write_control_file(self.index_basename, indexes.Index.to_string(new_index))
            if stats is not None:
                self.write_control_file(self.stats_basename, stats.to_string())
            else:
                self.delete_control_file(self.stats_basename)
            if diff:
                self.write_control_file(self.diff_basename, indexes.Diff.to_string(diff))
            self.success = True
        finally:
            self.postlaunch()
        return diff

    def command(self, command):
        with io.BytesIO() as fp:
            proc = subprocess.Popen(command, stdout=subprocess.PIPE,
                                    stderr=subprocess.PIPE, shell=True)
            for line in iter(proc.stdout.readline, ''):
                sys.stdout.write(line)
                fp.write(line)
            err = proc.stderr.read()
            if err:
                raise CommandError(err)
