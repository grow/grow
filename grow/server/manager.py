import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.common import sdk_utils
from grow.preprocessors import file_watchers
from grow.server import main as main_lib
from xtermcolor import colorize
from werkzeug import serving
import os
import socket
import sys
import threading


def shutdown(pod):
    pod.logger.info('Goodbye. Shutting down.')


from BaseHTTPServer import HTTPServer
from BaseHTTPServer import BaseHTTPRequestHandler


class CallbackHTTPServer(serving.ThreadedWSGIServer):

    def server_activate(self):
        HTTPServer.server_activate(self)
#            version = sdk_utils.get_this_version()
#            server.version = 'Grow/{}'.format(version)
#        self.RequestHandlerClass.post_activate()
        host, port = self.server_address
        self.pod.env.port = port
        self.pod.load()
        url = print_server_ready_message(self.pod, host, port)
        if self.open_browser:
            start_browser_in_thread(url)
#        if self.update_check:
#            thread = threading.Thread(target=sdk_utils.check_for_sdk_updates, args=(True,))
#            thread.setDaemon(True)
#            thread.start()


def start(pod, host=None, port=None, open_browser=False, debug=False,
          preprocess=True, update_check=False):
    observer, podspec_observer = file_watchers.create_dev_server_observers(pod)
    if preprocess:
        thread = threading.Thread(target=pod.preprocess, kwargs={'build': False})
        thread.setDaemon(True)
        thread.start()
    port = 8080 if port is None else int(port)
    host = 'localhost' if host is None else host
    port = find_free_port(host, port)
    if port is None:
        pod.logger.error('Unable to bind to {}:{}'.format(host, port))
        sys.exit(-1)
    CallbackHTTPServer.pod = pod
    CallbackHTTPServer.open_browser = open_browser
    CallbackHTTPServer.update_check = update_check
    serving.ThreadedWSGIServer = CallbackHTTPServer
    app = main_lib.create_wsgi_app(pod, debug=debug)
    serving.run_simple(host, port, app, request_handler=main_lib.RequestHandler, threaded=True)


def find_free_port(host, port):
    num_tries = 0
    test_socket = socket.socket()
    while num_tries < 10:
        try:
            test_socket.bind((host, port))
            test_socket.close()
            return port
        except socket.error as e:
            if 'Errno 48' in str(e):
                num_tries += 1
                port += 1
            else:
                raise e


def print_server_ready_message(pod, host, port):
    home_doc = pod.get_home_doc()
    if home_doc:
        root_path = home_doc.url.path
    else:
        root_path = pod.get_root_path()
    url = 'http://{}:{}{}'.format(host, port, root_path)
    logging.info('Pod: '.rjust(20) + pod.root)
    logging.info('Address: '.rjust(20) + url)
    ready_message = colorize('Server ready. '.rjust(20), ansi=47)
    logging.info(ready_message + 'Press ctrl-c to quit.')
    return url


def start_browser_in_thread(url):
    import webbrowser
    def _start_browser():
        webbrowser.open(url)
    thread = threading.Thread(target=_start_browser)
    thread.setDaemon(True)
    thread.start()
