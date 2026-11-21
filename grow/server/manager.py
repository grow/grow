"""Local development server manager."""

import importlib.metadata
import sys
import threading

from werkzeug import serving

from grow.common import colors, timer
from grow.preprocessors import file_watchers
from grow.server import main as main_lib


def _grow_version():
    try:
        return importlib.metadata.version('grow')
    except importlib.metadata.PackageNotFoundError:
        return ''


# Number of tries to find a free port.
NUM_TRIES = 10


class CallbackHTTPServer(serving.ThreadedWSGIServer):
    def server_activate(self):
        super().server_activate()
        _, port = self.server_address
        self.pod.env.port = port
        with timer.Timer() as router_time:
            try:
                self.pod.router.add_all(concrete=False)
            except Exception:
                self.pod.logger.exception('Error encountered starting server.')
                # Do not exit the process here; the server should remain active
                # so the developer can fix any issues related to the router,
                # without needing to manually restart the server.
        self.pod.logger.info(
            f'{len(self.pod.router.routes)} routes built in {router_time.secs:.3f} s'
        )

        url, extra_urls = print_server_ready_message(self.pod, self.pod.env.host, port)
        if self.open_browser:
            start_browser_in_thread(url)
            for extra_url in extra_urls:
                start_browser_in_thread(extra_url)


class ServerMessages:
    """Simple server messages."""

    def __init__(self):
        self.messages = []

    def add_message(self, label, message, label_color=None, message_color=None):
        self.messages.append((label, message, label_color, message_color))

    def print(self, log_function):
        label_max_width = max((len(label) for label, _, _, _ in self.messages), default=0)

        for label, message, label_color, message_color in self.messages:
            padded_label = label.ljust(label_max_width)
            if label_color:
                padded_label = colors.stylize(padded_label, label_color)
            if message_color:
                message = colors.stylize(message, message_color)
            arrow = colors.stylize('➜', colors.SUCCESS)
            log_function(f'  {arrow}  {padded_label}  {message}')


def print_server_ready_message(pod, host, port):
    try:
        home_doc = pod.get_home_doc()
        root_path = home_doc.url.path if home_doc and home_doc.exists else '/'
    except Exception:
        # Allow the user to fix the problem without restarting the server manually.
        root_path = '/'
        pod.logger.exception('Failed to determine root URL path.')
    url_base = f'http://{host}:{port}/'
    url_root = f'http://{host}:{port}{root_path}'
    url_console = f'http://{host}:{port}/_grow/'

    version = _grow_version()
    version_str = f' {colors.stylize(f"v{version}", colors.DIM)}' if version else ''
    header = (
        f'\n  {colors.stylize("Grow", colors.BRAND)}{version_str}  '
        f'{colors.stylize("dev server ready", colors.SUCCESS)}\n'
    )
    print(header)

    messages = ServerMessages()
    messages.add_message('Local:', url_root, colors.BOLD, colors.CYAN)
    messages.add_message('Console:', url_console, colors.BOLD, colors.CYAN)
    messages.add_message('Pod:', pod.root, colors.BOLD, colors.DIM)

    # Trigger the dev manager message hook.
    extra_urls = (
        pod.extensions_controller.trigger(
            'dev_manager_message', messages.add_message, url_base, url_root
        )
        or []
    )

    messages.print(print)
    print(f'\n  {colors.stylize("Press ctrl-c to quit.", colors.DIM)}\n')

    return (url_root, extra_urls)


def start(
    pod, host=None, port=None, open_browser=False, debug=False, preprocess=True, update_check=False
):
    main_observer, podspec_observer = file_watchers.create_dev_server_observers(pod)
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
    app = main_lib.create_wsgi_app(pod, host, port, debug=debug)
    serving._log = lambda *args, **kwargs: ''
    handler = main_lib.RequestHandler
    num_tries = 0
    done = False

    while num_tries < NUM_TRIES and not done:
        try:
            app.app.port = port
            serving.run_simple(host, port, app, request_handler=handler, threaded=True)
            done = True
        except OSError as e:
            # if any(x in str(e) for x in ('Errno 48', 'Errno 98')):
            if 'Errno 48' in str(e):
                num_tries += 1
                port += 1
            else:
                # Clean up the file watchers.
                main_observer.stop()
                podspec_observer.stop()
                raise e
        finally:
            if done:
                if pod.podcache.is_dirty:
                    pod.podcache.write()
                # Clean up the file watchers.
                main_observer.stop()
                podspec_observer.stop()
        if done:
            return

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
    from socketserver import BaseServer
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
