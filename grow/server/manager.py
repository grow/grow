import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.common import sdk_utils
from grow.preprocessors import file_watchers
from grow.server import main as main_lib
from werkzeug import serving
from xtermcolor import colorize
import os
import socket
import sys
import threading

# Number of tries to find a free port.
NUM_TRIES = 10


class CallbackHTTPServer(serving.ThreadedWSGIServer):

    def server_activate(self):
        super(CallbackHTTPServer, self).server_activate()
        host, port = self.server_address
        self.pod.env.port = port
        self.pod.load()
        url = print_server_ready_message(self.pod, self.pod.env.host, port)
        if self.open_browser:
            start_browser_in_thread(url)
        if self.update_check:
            check_func = sdk_utils.check_for_sdk_updates
            thread = threading.Thread(target=check_func, args=(True,))
            thread.start()


def print_server_ready_message(pod, host, port):
    home_doc = pod.get_home_doc()
    root_path = home_doc.url.path if home_doc else '/'
    url = 'http://{}:{}{}'.format(host, port, root_path)
    logging.info('Pod: '.rjust(20) + pod.root)
    logging.info('Address: '.rjust(20) + url)
    ready_message = colorize('Server ready. '.rjust(20), ansi=47)
    logging.info(ready_message + 'Press ctrl-c to quit.')
    return url


def start(pod, host=None, port=None, open_browser=False, debug=False,
          preprocess=True, update_check=False):
    observer, podspec_observer = file_watchers.create_dev_server_observers(pod)
    if preprocess:
        thread = threading.Thread(target=pod.preprocess, kwargs={'build': False})
        thread.setDaemon(True)
        thread.start()
    port = 8080 if port is None else int(port)
    host = 'localhost' if host is None else host
    patch_broken_pipe_error()
    # Not safe for multi-pod serving env.
    CallbackHTTPServer.pod = pod
    CallbackHTTPServer.open_browser = open_browser
    CallbackHTTPServer.update_check = update_check
    serving.ThreadedWSGIServer = CallbackHTTPServer
    app = main_lib.create_wsgi_app(pod, debug=debug)
    serving._log = lambda *args, **kwargs: ''
    handler = main_lib.RequestHandler
    num_tries = 0
    done = False
    while num_tries < NUM_TRIES and not done:
        try:
            serving.run_simple(host, port, app, request_handler=handler, threaded=True)
            done = True
        except socket.error as e:
            if 'Errno 48' in str(e):
                num_tries += 1
                port += 1
            else:
                raise e
        finally:
            # Ensure ctrl+c works no matter what.
            # https://github.com/grow/grow/issues/149
            if done:
                os._exit(0)
    text = 'Unable to find a port for the server (tried {}).'
    pod.logger.error(text.format(port))
    sys.exit(-1)


def start_browser_in_thread(url):
    def _start_browser():
        import webbrowser
        webbrowser.open(url)
    thread = threading.Thread(target=_start_browser)
    thread.setDaemon(True)
    thread.start()


def patch_broken_pipe_error():
    from SocketServer import BaseServer
    from wsgiref import handlers

    handle_error = BaseServer.handle_error
    log_exception = handlers.BaseHandler.log_exception

    def is_broken_pipe_error():
        _, err, _ = sys.exc_info()
        return repr(err) == "error(32, 'Broken pipe')"

    def patched_handle_error(self, request, client_address):
        if not is_broken_pipe_error():
            handle_error(self, request, client_address)

    def patched_log_exception(self, exc_info):
        if not is_broken_pipe_error():
            log_exception(self, exc_info)

    BaseServer.handle_error = patched_handle_error
    handlers.BaseHandler.log_exception = patched_log_exception
