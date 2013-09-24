#!/usr/bin/env python

import base64
import gflags as flags
import os
from google.apputils import appcommands
from grow.client import client
from grow.pods import commands as pod_commands
#from grow.deployment import google_cloud_storage
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

    # THIS IS TERRIBLE PLEASE THANKS!
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

  def Run(self, argv):
    if len(argv) != 3:
      raise Exception('Usage: grow dump <pod root> <out directory>')
    root = os.path.abspath(os.path.join(os.getcwd(), argv[-2]))
    out_dir = os.path.abspath(os.path.join(os.getcwd(), argv[-1]))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.dump(out_dir=out_dir)


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
