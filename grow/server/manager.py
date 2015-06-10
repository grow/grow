import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.pods.preprocessors import file_watchers
from grow.server import main as main_lib
from wsgiref import simple_server
from xtermcolor import colorize
import socket
import sys
import threading
import time
import webbrowser


class DevServerWSGIRequestHandler(simple_server.WSGIRequestHandler):
  _logging_enabled = False

  @staticmethod
  def sizeof(num):
    for x in ['b', 'KB', 'MB', 'GB', 'TB']:
      if num < 1024.0:
        return '%3.1f%s' % (num, x)
      num /= 1024.0

  def log_date_time_string(self):
    now = time.time()
    year, month, day, hh, mm, ss, x, y, z = time.localtime(now)
    return '%02d:%02d:%02d' % (hh, mm, ss)

  def log_request(self, code=0, size='-'):
    if not self._logging_enabled:
      return
    line = self.requestline[:-9]
    method, line = line.split(' ', 1)
    color = 19
    if int(code) >= 500:
      color = 161
    code = colorize(code, ansi=color)
    size = colorize(DevServerWSGIRequestHandler.sizeof(size), ansi=19)
    self.log_message('{} {} {}'.format(code, line, size))

  def log_message(self, format, *args):
    #  def log_error(self, format, *args)
    timestring = colorize(self.log_date_time_string(), ansi=241, ansi_bg=233)
    sys.stderr.write('%s %s\n' % (timestring, format % args))


def start(pod, host=None, port=None, open_browser=False, debug=False,
          preprocess=True):
  observer, podspec_observer = file_watchers.create_dev_server_observers(pod)
  if preprocess:
    # Run preprocessors for the first time in a thread.
    thread = threading.Thread(target=pod.preprocess)
    thread.start()

  try:
    # Create the development server.
    app = main_lib.CreateWSGIApplication(pod)
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
          port += 1
        else:
          raise e

  except Exception as e:
    logging.error('Failed to start server: {}'.format(e))
    observer.stop()
    observer.join()
    sys.exit()

  try:
    root_path = pod.get_root_path()
    url = 'http://{}:{}{}'.format(host, port, root_path)
    print 'Pod: '.rjust(20) + pod.root
    print 'Address: '.rjust(20) + url
    print colorize('Server ready. '.rjust(20), ansi=47) + 'Press ctrl-c to quit.'
    def start_browser(server_ready_event):
      server_ready_event.wait()
      if open_browser:
        webbrowser.open(url)
    server_ready_event = threading.Event()
    browser_thread = threading.Thread(target=start_browser,
                                      args=(server_ready_event,))
    browser_thread.start()
    server_ready_event.set()
    httpd.serve_forever()
    browser_thread.join()

  except KeyboardInterrupt:
    logging.info('Goodbye. Shutting down.')
    httpd.server_close()
    observer.stop()
    observer.join()

  # Clean up once server exits.
  sys.exit()
