#!/usr/bin/env python

import logging
import gflags as flags
import os
from google.apputils import appcommands
from grow.deployments import deployments
from grow.common import launchpad
from grow.common import sdk_utils
from grow.common import utils
from grow.server import manager
from grow.pods import commands as pod_commands
from grow.pods import pods
from grow.pods import storage


FLAGS = flags.FLAGS

flags.DEFINE_boolean(
    'skip_sdk_update_check', False, 'Whether to skip the check for SDK updates.')



class BuildCmd(appcommands.Cmd):
  """Generates static files and dumps them to a local destination."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_boolean(
        'dot_grow_dir', True, 'Whether to include the .grow dir in the build.',
        flag_values=flag_values)
    super(BuildCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-2]))
    out_dir = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.dump(out_dir=out_dir, include_dot_grow_dir=FLAGS.dot_grow_dir)


class DeployCmd(appcommands.Cmd):
  """Deploys a pod to a destination."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_boolean(
        'confirm', True, 'Whether to confirm prior to deployment.',
        flag_values=flag_values)
    flags.DEFINE_enum(
        'destination', None, ['gcs', 'local', 's3', 'zip'],
        'Destination to deploy to.',
        flag_values=flag_values)
    flags.DEFINE_string(
        'bucket', None, 'Google Cloud Storage or Amazon S3 bucket.',
        flag_values=flag_values)
    flags.DEFINE_string(
        'out_dir', None, 'Directory to write to.',
        flag_values=flag_values)
    flags.DEFINE_string(
        'out_file', None, 'File name of zip file to use.',
        flag_values=flag_values)
    super(DeployCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def _get_deployment_from_command_line(self):
    if FLAGS.destination is None:
      raise appcommands.AppCommandsError('Must specify: --destination.')
    elif FLAGS.destination == 'gcs':
      if FLAGS.bucket is None:
        raise appcommands.AppCommandsError('Must specify: --bucket.')
      deployment = deployments.GoogleCloudStorageDeployment(bucket=FLAGS.bucket)
    elif FLAGS.destination == 's3':
      if FLAGS.bucket is None:
        raise appcommands.AppCommandsError('Must specify: --bucket.')
      deployment = deployments.AmazonS3Deployment(bucket=FLAGS.bucket)
    elif FLAGS.destination == 'local':
      if FLAGS.out_dir is None:
        raise appcommands.AppCommandsError('Must specify: --out_dir.')
      out_dir = os.path.abspath(os.path.expanduser(FLAGS.out_dir))
      deployment = deployments.LocalDeployment(out_dir=out_dir)
    elif FLAGS.destination == 'zip':
      if FLAGS.out_dir is None and FLAGS.out_file is None:
        raise appcommands.AppCommandsError('Must specify either: --out_dir or --out_file.')
      out_dir = os.path.abspath(os.path.expanduser(FLAGS.out_dir)) if FLAGS.out_dir else None
      out_file = os.path.abspath(os.path.expanduser(FLAGS.out_file)) if FLAGS.out_file else None
      deployment = deployments.ZipFileDeployment(out_dir=out_dir, out_file=out_file)
    return deployment

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.preprocess()

    # Figure out if we're using the default deployment.
    if len(argv) == 2 and not FLAGS.destination:
      deployment_name = 'default'  # grow deploy .
    elif len(argv) == 3:
      deployment_name = argv[-2]   # grow deploy <name> .
    else:
      deployment_name = None       # grow deploy --destination=<kind> .

    if deployment_name:
      deployment = pod.get_deployment(deployment_name)
    else:
      deployment = self._get_deployment_from_command_line()
    deployment.deploy(pod, confirm=FLAGS.confirm)


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

  def Run(self, argv):
    if len(argv) != 3:
      raise Exception('Usage: grow init <repo> <pod root>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    theme_url = argv[-2]
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod_commands.init(pod, theme_url)


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
      sdk_utils.check_version(auto_update_prompt=True)
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
    text = ('---\n{red}WARNING!{/red} Use machine translation with caution.'
            ' It is not intended for use in production.\n---')
    logging.info(utils.colorize(text))
    translations = pod.get_translations()
    translations.extract()
    for locale in FLAGS.locale:
      translation = translations.get_translation(locale)
      translation.update_catalog()
      translation.machine_translate()


class UpCmd(appcommands.Cmd):
  """Uploads a pod to a launchpad server."""

  def __init__(self, name, flag_values, command_aliases=None):
    flags.DEFINE_string(
        'host', 'grow-prod.appspot.com', 'Launchpad hostname.',
        flag_values=flag_values)
    super(UpCmd, self).__init__(name, flag_values, command_aliases=command_aliases)

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    session = launchpad.Launchpad(FLAGS.host)
    session.create_fileset(pod)


def add_commands():
  appcommands.AddCmd('build', BuildCmd)
  appcommands.AddCmd('deploy', DeployCmd)
  appcommands.AddCmd('extract', ExtractCmd)
  appcommands.AddCmd('machine_translate', MachineTranslateCmd)
  appcommands.AddCmd('init', InitCmd)
  appcommands.AddCmd('run', RunCmd)
  appcommands.AddCmd('routes', RoutesCmd)
  appcommands.AddCmd('up', UpCmd)
  appcommands.AddCmd('test', TestCmd)
