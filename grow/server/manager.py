import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.pods.preprocessors import translation as translation_preprocessor
from grow.pods.preprocessors.file_watchers import file_watchers
from grow.server import handlers
from grow.server import main as main_lib
from wsgiref import simple_server
from xtermcolor import colorize
import os
import socket
import sys
import threading
import time
import webbrowser

_servers = {}


def _watch_for_changes(pod, file_watchers_to_preprocessors, quit_event):
  while not quit_event.is_set():
    for file_watcher, preprocessors in file_watchers_to_preprocessors.iteritems():
      if file_watcher.has_changes():
        [preprocessor.run() for preprocessor in preprocessors]
    quit_event.wait(timeout=1.5)

def sizeof(num):
  for x in ['b', 'KB', 'MB', 'GB', 'TB']:
    if num < 1024.0:
      return '%3.1f%s' % (num, x)
    num /= 1024.0


class DevServerWSGIRequestHandler(simple_server.WSGIRequestHandler):

#  def log_error(self, format, *args):

  def log_date_time_string(self):
    now = time.time()
    year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
    return '%02d:%02d:%02d' % (hh, mm, ss)

  def log_request(self, code=0, size='-'):
    line = self.requestline[:-9]
    method, line = line.split(' ', 1)
    color = 19
    if int(code) >= 500:
      color = 161
    code = colorize(code, ansi=color)
    size = colorize(sizeof(size), ansi=19)
    self.log_message('{} {} {}'.format(code, line, size))

  def log_message(self, format, *args):
    timestring = colorize(self.log_date_time_string(), ansi=241, ansi_bg=233)
    sys.stderr.write('%s %s\n' % (timestring, format % args))


def start(pod, host=None, port=None, open_browser=False):
  print ''
  print '  The Grow SDK is experimental. Expect backwards incompatibility until v0.1.0.'
  print '  Thank you for testing and contributing! Visit http://growsdk.org for resources.'
  print ''

  root = pod.root
  preprocessors = pod.list_preprocessors()

  # Add the translation preprocessor as a builtin.
  preprocessors.insert(0, translation_preprocessor.TranslationPreprocessor(pod=pod))

  try:
    # Map directory names to preprocessors.
    dirs_to_preprocessors = {}
    for preprocessor in preprocessors:
      for watched_dir in preprocessor.list_watched_dirs():
        if watched_dir not in dirs_to_preprocessors:
          dirs_to_preprocessors[watched_dir] = []
        dirs_to_preprocessors[watched_dir].append(preprocessor)

    # Run all preprocessors for the pod.
    for preprocessor in preprocessors:
      thread = threading.Thread(target=preprocessor.first_run)
      thread.start()
      thread.join()

    # Create file watchers for each preprocessor.
    file_watchers_to_preprocessors = {}
    for dirname, preprocessors in dirs_to_preprocessors.iteritems():
      dirname = os.path.join(pod.root, dirname.lstrip('/'))
      change_watcher = file_watchers.get_file_watcher([dirname])
      change_watcher.start()
      file_watchers_to_preprocessors[change_watcher] = preprocessors

    # Start a thread where preprocessors can run if there are changes.
    quit_event = threading.Event()
    change_watcher_thread = threading.Thread(
        target=_watch_for_changes,
        args=(pod, file_watchers_to_preprocessors, quit_event))
    change_watcher_thread.start()

    # Create the development server.
    root = os.path.abspath(os.path.normpath(root))
    handlers.set_pod_root(root)
    app = main_lib.application
    port = 8080 if port is None else int(port)
    host = 'localhost' if host is None else host
    num_tries = 0
    while num_tries < 10:
      try:
        httpd = simple_server.make_server(host, port, app,
                                          handler_class=DevServerWSGIRequestHandler)
        num_tries = 99
      except socket.error as e:
        if e.errno == 48:
          num_tries += 1
          old_port = port
          port += 1
          logging.info("Couldn't use port {}, trying {} instead...".format(old_port, port))
        else:
          raise e

  except Exception as e:
    logging.error('Failed to start server: {}'.format(e))
    quit_event.set()
    change_watcher_thread.join()
    sys.exit()

  try:
    root_path = pod.get_root_path()
    url = 'http://{}:{}{}'.format(host, port, root_path)
    message = 'Serving pod {} @ {}'.format(root, colorize(url, ansi=99))
    print colorize('Ready! ', ansi=47) + message

    def start_browser(server_ready_event):
      server_ready_event.wait()
      if open_browser:
        webbrowser.open(url)

    server_ready_event = threading.Event()
    browser_thread = threading.Thread(target=start_browser, args=(server_ready_event,))
    browser_thread.start()
    server_ready_event.set()
    httpd.serve_forever()
    browser_thread.join()

  except KeyboardInterrupt:
    logging.info('Shutting down...')
    httpd.server_close()

  # Clean up once serve exits.
  quit_event.set()
  change_watcher_thread.join()
  sys.exit()
