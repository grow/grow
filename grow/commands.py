#!/usr/bin/env python

from google.apputils import appcommands
from grow.common import sdk_utils
from grow.deployments.destinations import local as local_destination
from grow.deployments.stats import stats
from grow.pods import commands as pod_commands
from grow.pods import pods
from grow.pods import storage
from grow.server import manager
from xtermcolor import colorize
import gflags as flags
import git
import logging
import os
import threading


FLAGS = flags.FLAGS

flags.DEFINE_boolean(
    'skip_sdk_update_check', False, 'Whether to skip the check for SDK updates.')

def _get_git_repo(root):
  try:
    return git.Repo(root)
  except git.exc.InvalidGitRepositoryError:
    logging.info('Warning: {} is not a Git repository.'.format(root))


class BuildCmd(appcommands.Cmd):
  """Generates static files and dumps them to a local destination."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_string(
        'out_dir', None, 'Where to build to.', flag_values=flag_values)
    super(BuildCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    out_dir = FLAGS.out_dir or os.path.join(root, 'build')
    pod = pods.Pod(root, storage=storage.FileStorage)
    paths_to_contents = pod.dump()
    repo = _get_git_repo(pod.root)
    config = local_destination.Config(out_dir=out_dir)
    stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
    destination = local_destination.LocalDestination(config, run_tests=False)
    destination.deploy(paths_to_contents, stats=stats_obj, repo=repo, confirm=False)


class DeployCmd(appcommands.Cmd):
  """Deploys a pod to a destination."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_boolean(
        'test', False, 'Whether to only run the deployment tests.',
        flag_values=flag_values)
    flags.DEFINE_boolean(
        'confirm', True, 'Whether to confirm prior to deployment.',
        flag_values=flag_values)
    super(DeployCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.preprocess()

    # Figure out if we're using the default deployment.
    if len(argv) == 2:
      deployment_name = 'default'  # grow deploy .
    elif len(argv) == 3:
      deployment_name = argv[-2]   # grow deploy <name> .
    else:
      raise Exception('Invalid command.')

    deployment = pod.get_deployment(deployment_name)

    if FLAGS.test:
      deployment.test()
    else:
      paths_to_contents = pod.dump()
      repo = _get_git_repo(pod.root)
      stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
      deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                        confirm=FLAGS.confirm)


class ExtractCmd(appcommands.Cmd):
  """Extracts a pod's translations into messages files."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_boolean(
        'init', False,
        'Whether to init catalogs (wipes out existing translations) or '
        'update them (merges new strings into existing catalogs).',
        flag_values=flag_values)
    super(ExtractCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translations = pod.get_translations()
    translations.extract()
    locales = pod.list_locales()
    if not locales:
      logging.info('No pod-specific locales defined, '
                   'skipped generating locale-specific catalogs.')
    else:
      if FLAGS.init:
        translations.init_catalogs(locales)
      else:
        translations.update_catalogs(locales)


class InitCmd(appcommands.Cmd):
  """Initializes a pod using a theme, ready for development."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_boolean(
        'force', False,
        'Whether to overwrite any existsing files and directories in the pod.')
    super(InitCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    if len(argv) != 3:
      raise Exception('Usage: grow init <repo> <pod root>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    theme_url = argv[-2]
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod_commands.init(pod, theme_url, force=FLAGS.force)


class RoutesCmd(appcommands.Cmd):
  """Lists routes defined by a pod."""

  def Run(self, argv):
    if len(argv) != 2:
      raise Exception('Usage: grow routes <pod root>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    routes = pod.get_routes()
    logging.info(routes.to_message())


class RunCmd(appcommands.Cmd):
  """Starts a pod server for a single pod."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_string(
        'host', 'localhost', 'IP address or hostname to bind the server to.',
        flag_values=flag_values)
    flags.DEFINE_integer(
        'port', '8080', 'Port to start the server on.',
        flag_values=flag_values)
    flags.DEFINE_boolean(
        'open', False,
        'Whether to open a web browser when starting the server.')
    super(RunCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    if len(argv) != 2:
      # Default to using the current directory as the root for the pod.
      root = os.path.abspath(os.getcwd())
    else:
      root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    if not FLAGS.skip_sdk_update_check:
      thread = threading.Thread(target=sdk_utils.check_version, args=(True,))
      thread.start()
    pod = pods.Pod(root, storage=storage.FileStorage)
    manager.start(pod, host=FLAGS.host, port=FLAGS.port, open_browser=FLAGS.open)


class TestCmd(appcommands.Cmd):
  """Validates a pod and runs its tests."""

  def Run(self):
    raise NotImplementedError()


class MachineTranslateCmd(appcommands.Cmd):
  """Translates a message catalog using machine translation."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_multistring('locale', [], 'Which locale to translate.',
                             flag_values=flag_values)
    super(MachineTranslateCmd, self).__init__(
        name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    if not FLAGS.locale:
      raise appcommands.AppCommandsError('Must specify: --locale.')
    translations = pod.get_translations()
    translations.extract()
    for locale in FLAGS.locale:
      translation = translations.get_translation(locale)
      translation.update_catalog()
      translation.machine_translate()
    print ''
    print colorize('  WARNING! Use machine translations with caution.', ansi=197)
    print colorize('  Machine translations are not intended for use in production.', ansi=197)
    print ''


def add_commands():
  appcommands.AddCmd('build', BuildCmd)
  appcommands.AddCmd('deploy', DeployCmd)
  appcommands.AddCmd('extract', ExtractCmd)
  appcommands.AddCmd('machine_translate', MachineTranslateCmd)
  appcommands.AddCmd('init', InitCmd)
  appcommands.AddCmd('run', RunCmd)
  appcommands.AddCmd('routes', RoutesCmd)
  appcommands.AddCmd('test', TestCmd)
