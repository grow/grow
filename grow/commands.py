#!/usr/bin/env python

import base64
import gflags as flags
import logging
import os
from google.apputils import appcommands
from grow import deployments
from grow.client import client
from grow.pods import commands as pod_commands
from grow.pods import pods
from grow.pods import storage
from grow.server import handlers
from grow.server import main as main_lib
from paste import httpserver

FLAGS = flags.FLAGS
flags.DEFINE_string('changeset', None, 'Changeset name.')
flags.DEFINE_string('host', None, 'Grow server hostname (e.g. example.com).')



class UpCmd(appcommands.Cmd):

  def Run(self, argv):
    changeset = FLAGS.changeset
    host = FLAGS.host
    pod = pods.Pod(argv[1], storage=storage.FileStorage)

    # TODO(jeremydw): Fix this.
    if host is not None and 'localhost' in host:
      service = client.get_service(host=FLAGS.host)
      for pod_path in pod.list_files_in_pod():
        path = pod.get_abspath(pod_path)
        content = open(path).read()
        content = base64.b64encode(content)
        req = service.pods().writefile(body={
           'pod': {'changeset': changeset},
           'file_transfer': {
             'pod_path': pod_path,
             'content_b64': content,
           },
        })
        req.execute()
        print 'Uploaded: {}'.format(pod_path)
      req = service.pods().finalizeStagedFiles(body={
        'pod': {'changeset': changeset}
      })
      req.execute()
      print 'Upload finalized.'
    else:
      google_cloud_storage.upload_to_gcs(pod, changeset, host=host)


class RunCmd(appcommands.Cmd):

  def Run(self, argv):
    if len(argv) != 2:
      raise Exception('Must specify pod directory.')

    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    handlers.set_single_pod_root(root)
    print 'Serving pod with root: {}'.format(root)

    httpserver.serve(main_lib.application)


class DumpCmd(appcommands.Cmd):

  flags.DEFINE_string('destination', None,
                      'Destination to dump to.')

  flags.DEFINE_string('bucket', None,
                      'Google Cloud Storage or Amazon S3 bucket.')

  def Run(self, argv):
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)

    if FLAGS.destination is None:
      raise appcommands.AppCommandsError('Must specify: --destination.')

    if FLAGS.destination == 'gcs':
      deployment = deployments.GoogleCloudStorageDeployment(bucket=FLAGS.bucket)
    else:
      out_dir = os.path.abspath(os.path.join(os.getcwd(), FLAGS.destination))
      deployment = deployments.FileSystemDeployment(out_dir=out_dir)

    deployment.dump(pod)
    return


class InitCmd(appcommands.Cmd):

  flags.DEFINE_string('repo_url', pod_commands.REPO_URL,
                      'URL to repo containing Grow templates.')

  def Run(self, argv):
    if len(argv) != 3:
      raise Exception('Usage: grow init <branch> <pod root>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    branch_name = argv[-2]
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod_commands.init(pod, branch_name)


class GetCmd(appcommands.Cmd):

  def Run(self):
    pass
