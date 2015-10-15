import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.pods.preprocessors import file_watchers
from grow.server import main as main_lib
from twisted.internet import reactor
from twisted.web import server
from twisted.web import wsgi
from xtermcolor import colorize
import sys
import threading
import twisted
import webbrowser


def start(pod, host=None, port=None, open_browser=False, debug=False,
          preprocess=True):
  observer, podspec_observer = file_watchers.create_dev_server_observers(pod)
  if preprocess:
    # Run preprocessors for the first time in a thread.
    thread = threading.Thread(target=pod.preprocess)
    thread.start()
  port = 8080 if port is None else int(port)
  host = 'localhost' if host is None else host
  port = find_port_and_start_server(pod, host, port, debug)
  url = print_server_ready_message(pod, host, port)
  if open_browser:
    start_browser(url)
  reactor.run()
  pod.logger.info('Goodbye. Shutting down.')


def find_port_and_start_server(pod, host, port, debug):
  # Thread pool must be size 1 until a hard-to-pin down bug involving
  # thread safety and static asset responses is fixed.
  reactor.suggestThreadPoolSize(1)
  app = main_lib.CreateWSGIApplication(pod, debug=debug)
  num_tries = 0
  while num_tries < 10:
    try:
      wsgi_resource = wsgi.WSGIResource(reactor, reactor.getThreadPool(), app)
      reactor.listenTCP(port, server.Site(wsgi_resource), interface=host)
      return port
    except twisted.internet.error.CannotListenError as e:
      if 'Errno 48' in str(e):
        num_tries += 1
        port += 1
      else:
        raise e
  pod.logger.error('Unable to bind to {}:{}'.format(host, port))
  sys.exit(-1)


def print_server_ready_message(pod, host, port):
  home_doc = pod.get_home_doc()
  if home_doc:
    root_path = home_doc.url.path
  else:
    root_path = pod.get_root_path()
  url = 'http://{}:{}{}'.format(host, port, root_path)
  print 'Pod: '.rjust(20) + pod.root
  print 'Address: '.rjust(20) + url
  print colorize('Server ready. '.rjust(20), ansi=47) + 'Press ctrl-c to quit.'
  return url


def start_browser(url):
  def _start_browser(server_ready_event):
    server_ready_event.wait()
    webbrowser.open(url)
  server_ready_event = threading.Event()
  browser_thread = threading.Thread(
      target=_start_browser, args=(server_ready_event,))
  browser_thread.start()
  server_ready_event.set()
