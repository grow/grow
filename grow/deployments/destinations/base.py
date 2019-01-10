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

  write_file(self, rendered_doc)
    Writes a file at the destination, given the file's rendered_document.

  write_files(self, paths_to_rendered_doc)
    Writes files in bulk, given a mapping of paths to rendered_document.

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

import inspect
import io
import json
import logging
import os
import subprocess
import re
import sys
from grow.common import utils
from grow.deployments import indexes
from grow.deployments import tests
from grow.performance import profile_report
from grow.pods import env
from grow.pods import pods
from grow.rendering import rendered_document
from . import messages


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
    """Base destination for building and deploying."""

    TestCase = DestinationTestCase
    diff_basename = 'diff.proto.json'
    index_basename = 'index.proto.json'
    stats_basename = 'stats.proto.json'
    threaded = True
    batch_writes = False
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
            control_dir = pods.Pod.PATH_CONTROL
            return os.path.join(self.pod.root, control_dir, 'deployments', self.name)
        if self._has_custom_control_dir:
            return self.config.control_dir
        return pods.Pod.PATH_CONTROL

    @property
    def prevent_untranslated(self):
        """Configuration for untranslated messages preventing deployment."""
        if not self.config.base_config:
            return False
        return self.config.base_config.prevent_untranslated

    @property
    def storage(self):
        raise NotImplementedError

    def _get_remote_index(self):
        try:
            content = self.read_control_file(self.index_basename)
            return indexes.Index.from_string(content)
        except IOError:
            logging.info('Unable to find remote index: {}'.format(
                self.index_basename))
            return indexes.Index.create()

    def export_profile_report(self):
        """Write the results of the profiling timers."""
        report = profile_report.ProfileReport(self.pod.profile)
        file_name = '{}profile.json'.format(self.control_dir)
        self.pod.write_file(file_name, json.dumps(report.export()))
        logging.info('Profiling data exported to {}'.format(file_name))

    def export_untranslated_catalogs(self):
        dir_path = '{}untranslated/'.format(self.control_dir)
        catalogs = self.pod.translation_stats.export_untranslated_catalogs(
            self.pod, dir_path=dir_path)
        self.pod.delete_files([dir_path], recursive=True,
                              pattern=re.compile(r'\.po$'))
        for _, catalog in catalogs.iteritems():
            catalog.save()
        if self.pod.translation_stats.stacktraces:
            self.pod.write_file(os.path.join(dir_path, 'tracebacks.log'),
                self.pod.translation_stats.export_untranslated_tracebacks())
        if catalogs or self.pod.translation_stats.stacktraces:
            logging.info('Untranslated strings exported to {}'.format(dir_path))

    def get_env(self):
        """Returns an environment object based on the config."""
        if self.config.env:
            return env.Env(self.config.env)
        config = env.EnvConfig(host='localhost')
        return env.Env(config)

    def read_file(self, path):
        """Returns a file-like object."""
        raise NotImplementedError

    def write_files(self, paths_to_rendered_doc):
        """Writes files in bulk."""
        raise NotImplementedError

    def write_file(self, rendered_doc):
        """Writes an individual file."""
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
            return self.write_files({
                path: rendered_document.RenderedDocument(path, content)
            })
        return self.write_file(
            rendered_document.RenderedDocument(path, content))

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

    def dump(self, pod, pod_paths=None, use_threading=True):
        pod.set_env(self.get_env())
        return pod.dump(pod_paths=pod_paths, use_threading=use_threading)

    def deploy(self, content_generator, stats=None, repo=None, dry_run=False,
               confirm=False, test=True, is_partial=False, require_translations=False):
        self._confirm = confirm
        self.prelaunch(dry_run=dry_run)
        if test:
            self.test()
        try:
            deployed_index = self._get_remote_index()
            if require_translations:
                self.pod.enable(self.pod.FEATURE_TRANSLATION_STATS)
            diff, new_index, paths_to_rendered_doc = indexes.Diff.stream(
                deployed_index, content_generator, repo=repo, is_partial=is_partial)
            self._diff = diff
            if indexes.Diff.is_empty(diff):
                logging.info('Finished with no diffs since the last build.')
                return
            if dry_run:
                return
            indexes.Diff.pretty_print(diff)
            if require_translations and self.pod.translation_stats.untranslated:
                self.pod.translation_stats.pretty_print()
                raise pods.Error('Aborted deploy due to untranslated strings. '
                                 'Use the --force-untranslated flag to force deployment.')
            if confirm:
                text = 'Proceed to deploy? -> {}'.format(self)
                if not utils.interactive_confirm(text):
                    logging.info('Aborted.')
                    return
            indexes.Diff.apply(
                diff, paths_to_rendered_doc, write_func=self.write_file,
                batch_write_func=self.write_files, delete_func=self.delete_file,
                threaded=self.threaded, batch_writes=self.batch_writes)
            self.write_control_file(
                self.index_basename, indexes.Index.to_string(new_index))
            if stats is not None:
                self.write_control_file(self.stats_basename, stats.to_string())
            else:
                self.delete_control_file(self.stats_basename)
            if diff:
                self.write_control_file(
                    self.diff_basename, indexes.Diff.to_string(diff))
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
