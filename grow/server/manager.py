import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.server import handlers
from grow.server import main as main_lib
from paste import httpserver
import atexit
import multiprocessing
import os
import yaml

_servers = {}
_config_path = '{}/.grow/servers'.format(os.environ['HOME'])


def start(root, port=None, use_subprocess=False):
  if root in _servers:
    logging.error('Server already started for pod: {}'.format(root))
    return
  root = os.path.abspath(os.path.normpath(root))
  handlers.set_single_pod_root(root)
  if not use_subprocess:
    httpserver.serve(main_lib.services_app)
    return
  logging.info('Started server for pod: {}'.format(root))
  process = multiprocessing.Process(
      target=httpserver.serve,
      args=(main_lib.services_app,))
  process.start()
  _servers[root] = process


def stop(root):
  process = _servers[root]
  process.terminate()
  del _servers[root]
  logging.info('Stopped server for pod: {}'.format(root))


@atexit.register
def stop_all():
  for root in _servers.keys():
    stop(root)


def read_config():
  return yaml.load(_config_path)


def write_config(config):
  path = os.path.dirname(_config_path)
  if not os.path.exists(path):
    os.makedirs(path)
  content = yaml.dump(config, default_flow_style=False)
  fp = open(_config_path, 'w')
  fp.write(content)
  fp.close()


class Pod(object):

  def __init__(self, root, port=8000):
    self.root = root
    self.port = port

  @property
  def revision_status(self):
    pass

  @property
  def server_status(self):
    return 'off'

  def start_server(self):
    pass

  def stop_server(self):
    pass

  def set_root(self, root):
    self.root = root

  def set_port(self, port):
    self.port = port
