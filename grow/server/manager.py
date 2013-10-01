import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.server import handlers
from grow.server import main as main_lib
from paste import httpserver
import atexit
import multiprocessing
import os

_servers = {}


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
