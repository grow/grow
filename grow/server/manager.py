import logging
logging.basicConfig(level=logging.INFO, format='%(message)s')

from grow.common import sdk_utils
from grow.preprocessors import file_watchers
from grow.server import main as main_lib
from twisted.internet import reactor
from twisted.web import server
from twisted.web import wsgi
from xtermcolor import colorize
import sys
import threading
import twisted
import webbrowser


def shutdown(pod):
    pod.logger.info('Goodbye. Shutting down.')


def start(pod, host=None, port=None, open_browser=False, debug=False,
          preprocess=True, update_check=False):
    observer, podspec_observer = file_watchers.create_dev_server_observers(pod)
    if preprocess:
        # Run preprocessors for the first time in a thread.
        reactor.callInThread(pod.preprocess, build=False)
    port = 8080 if port is None else int(port)
    host = 'localhost' if host is None else host
    port = find_port_and_start_server(pod, host, port, debug)
    pod.env.port = port
    pod.load()
    url = print_server_ready_message(pod, host, port)
    if open_browser:
        start_browser(url)
    shutdown_func = lambda *args: shutdown(pod)
    reactor.addSystemEventTrigger('during', 'shutdown', shutdown_func)
    if update_check:
        reactor.callInThread(sdk_utils.check_for_sdk_updates, True)
    reactor.run()


def find_port_and_start_server(pod, host, port, debug):
    app = main_lib.create_wsgi_app(pod, debug=debug)
    num_tries = 0
    while num_tries < 10:
        try:
            thread_pool = reactor.getThreadPool()
            wsgi_resource = wsgi.WSGIResource(reactor, thread_pool, app)
            site = server.Site(wsgi_resource)
            version = sdk_utils.get_this_version()
            server.version = 'Grow/{}'.format(version)
            reactor.listenTCP(port, site, interface=host)
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
    logging.info('Pod: '.rjust(20) + pod.root)
    logging.info('Address: '.rjust(20) + url)
    ready_message = colorize('Server ready. '.rjust(20), ansi=47)
    logging.info(ready_message + 'Press ctrl-c to quit.')
    return url


def start_browser(url):
    def _start_browser(server_ready_event):
        server_ready_event.wait()
        webbrowser.open(url)
    server_ready_event = threading.Event()
    reactor.callInThread(_start_browser, server_ready_event)
    server_ready_event.set()
