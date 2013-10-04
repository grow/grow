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
_config_path = '{}/.grow/servers.yaml'.format(os.environ['HOME'])


def _start(root, port):
  root = os.path.abspath(os.path.normpath(root))
  handlers.set_single_pod_root(root)
  httpserver.serve(main_lib.services_app)


def start(root, port=None, use_subprocess=False):
  if root in _servers:
    logging.error('Server already started for pod: {}'.format(root))
    return
  if not use_subprocess:
    httpserver.serve(main_lib.services_app)
    return
  process = multiprocessing.Process(target=_start, args=(root, port))
  process.start()
  _servers[root] = process
  return process


def stop(root):
  process = _servers.pop(root, None)
  if process is None:
    return
  try:
    process.terminate()
    logging.info('Stopped server for pod: {}'.format(root))
  except AttributeError:
    logging.info('Server already stopped for pod: {}'.format(root))


@atexit.register
def stop_all():
  for root in _servers.keys():
    stop(root)


def write_config(config):
  path = os.path.dirname(_config_path)
  if not os.path.exists(path):
    os.makedirs(path)
  content = yaml.dump(config, default_flow_style=False)
  fp = open(_config_path, 'w')
  fp.write(content)
  fp.close()



class PodServer(object):

  def __init__(self, root, port=8000, revision_status=None):
    self.root = root
    self.port = port
    self.revision_status = revision_status
    self.server_status = 'off'
    self._process = None

  def start(self):
    self._process = start(self.root, port=self.port, use_subprocess=True)
    self.server_status = 'on'
    logging.info('Started server for pod: {}'.format(self.root))

  def stop(self):
    self.server_status = 'off'
    try:
      self._process.terminate()
      logging.info('Stopped server for pod: {}'.format(self.root))
    except AttributeError:
      logging.info('Server already stopped.')

  def set_root(self, root):
    self.root = root

  def set_port(self, port):
    self.port = port

  @property
  def is_started(self):
    return self.server_status == 'on'

  @classmethod
  def load(cls):
    servers = []
    fp = open(_config_path)
    for server in yaml.load(fp)['servers']:
      servers.append(cls(
          server['root'],
          port=server.get('port'),
          revision_status=server.get('revision_status')
      ))
    return servers
