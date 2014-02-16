#!/usr/bin/env python

import logging
import base64
import gflags as flags
import os
from google.apputils import appcommands
from grow import deployments
from grow.client import client
from grow.common import sdk_utils
from grow.server import manager
from grow.pods import commands as pod_commands
from grow.pods import pods
from grow.pods import storage

FLAGS = flags.FLAGS

flags.DEFINE_boolean(
    'skip_sdk_update_check', False, 'Whether to skip the check for SDK updates.')



class DeployCmd(appcommands.Cmd):
  """Deploys a pod to a destination."""

  flags.DEFINE_boolean(
      'confirm', True, 'Whether to skip the deployment confirmation.')

  flags.DEFINE_enum(
      'destination', None, ['gcs', 'local', 's3'], 'Destination to deploy to.')

  flags.DEFINE_string(
      'bucket', None, 'Google Cloud Storage or Amazon S3 bucket.')

  flags.DEFINE_string(
      'out_dir', None, 'Directory to write to.')

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)

    if FLAGS.destination is None:
      raise appcommands.AppCommandsError('Must specify: --destination.')

    elif FLAGS.destination == 'gcs':
      if FLAGS.bucket is None:
        raise appcommands.AppCommandsError('Must specify: --bucket.')
      deployment = deployments.GoogleCloudStorageDeployment(confirm=FLAGS.confirm)
      deployment.set_params(bucket=FLAGS.bucket)

    elif FLAGS.destination == 's3':
      if FLAGS.bucket is None:
        raise appcommands.AppCommandsError('Must specify: --bucket.')
      deployment = deployments.AmazonS3Deployment(confirm=FLAGS.confirm)
      deployment.set_params(bucket=FLAGS.bucket)

    elif FLAGS.destination == 'local':
      if FLAGS.out_dir is None:
        raise appcommands.AppCommandsError('Must specify: --out_dir.')
      out_dir = os.path.abspath(os.path.join(os.getcwd(), FLAGS.out_dir))
      deployment = deployments.FileSystemDeployment(confirm=FLAGS.confirm)
      deployment.set_params(out_dir=out_dir)

    deployment.deploy(pod)


class DumpCmd(appcommands.Cmd):
  """Generates static files and dumps them to a local destination."""

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-2]))
    out_dir = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.dump(out_dir=out_dir)


class InitCmd(appcommands.Cmd):
  """Initializes a blank pod (or one with a theme) for local development."""

  def Run(self, argv):
    if len(argv) != 3:
      raise Exception('Usage: grow init <repo> <pod root>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    theme_url = argv[-2]
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod_commands.init(pod, theme_url)


class RoutesCmd(appcommands.Cmd):
  """Lists routes managed by a pod."""

  def Run(self, argv):
    if len(argv) != 2:
      raise Exception('Usage: grow routes <pod root>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    routes = pod.get_routes()
    logging.info(routes.to_message())


class RunCmd(appcommands.Cmd):
  """Starts a pod server for a single pod."""

  flags.DEFINE_string(
      'host', '127.0.0.1', 'IP address or hostname to bind the server to.')

  flags.DEFINE_integer(
      'port', None, 'Port to start the server on.')

  def Run(self, argv):
    if len(argv) != 2:
      raise Exception('Must specify pod directory.')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    sdk_utils.check_version(quiet=True)
    manager.start(root, host=FLAGS.host, port=FLAGS.port)


class TestCmd(appcommands.Cmd):
  """Validates a pod and runs its tests."""

  def Run(self):
    raise NotImplementedError()


class UpCmd(appcommands.Cmd):
  """Uploads a pod to a pod server."""

  flags.DEFINE_string(
      'remote_host', None, 'Pod server hostname (e.g. example.com).')

  flags.DEFINE_string(
      'project', None, 'Project ID (owner/name).')

  SKIP_PATTERNS = (
      '.DS_Store',
  )

  def Run(self, argv):
    owner, nickname = FLAGS.project.split('/')
    host = FLAGS.remote_host
    pod = pods.Pod(argv[1], storage=storage.FileStorage)

    # Uploading to GrowEdit on dev appserver.
    if True or (host is not None and 'localhost' in host):
      service = client.Client(host=FLAGS.remote_host)
      for pod_path in pod.list_dir('/'):
        if os.path.basename(pod_path) in UpCmd.SKIP_PATTERNS:
          continue
        path = os.path.join(pod.root, pod_path)
        content = open(path).read()
        if isinstance(content, unicode):
          content = content.encode('utf-8')
        content = base64.b64encode(content)
        service.rpc('pods.update_file', {
           'project': {
             'owner': {'nickname': owner},
             'nickname': nickname,
           },
           'file': {
             'pod_path': pod_path,
             'content_b64': content,
           }
        })
        print 'Uploaded: {}'.format(pod_path)
#      req = service.pods().finalizeStagedFiles(body={
#        'pod': {'changeset': changeset}
#      })
#      req.execute()
      print 'Upload finalized.'
    else:
      raise NotImplementedError()
#      google_cloud_storage.upload_to_gcs(pod, changeset, host=host)


def add_commands():
  appcommands.AddCmd('deploy', DeployCmd)
  appcommands.AddCmd('dump', DumpCmd)
  appcommands.AddCmd('init', InitCmd)
  appcommands.AddCmd('run', RunCmd)
  appcommands.AddCmd('routes', RoutesCmd)
  appcommands.AddCmd('up', UpCmd)
  appcommands.AddCmd('test', TestCmd)
