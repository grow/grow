"""Grow local development server."""

import os
import time
from urllib import parse as url_parse

from werkzeug import serving
from werkzeug.middleware import shared_data

import grow
from grow.common import colors, utils
from grow.pods import errors
from grow.server import handlers


# Use Grow's concise Root.js-style request logging instead of Werkzeug's default.
class RequestHandler(serving.WSGIRequestHandler):
    @property
    def server_version(self):
        return f'Grow/{grow.__version__}'

    def log(self, type, message, *args):
        pass

    def log_request(self, code='-', size='-'):
        status = str(code)
        if status.startswith('2'):
            code_str = colors.stylize(status, colors.SUCCESS)
        elif status.startswith('3'):
            code_str = colors.stylize(status, colors.CYAN)
        elif status.startswith('4'):
            code_str = colors.stylize(status, colors.CAUTION)
        else:
            code_str = colors.stylize(status, colors.ERROR)

        method = getattr(self, 'command', 'GET')
        path = getattr(self, 'path', '')
        elapsed_ms = ''
        start = getattr(self, '_grow_start_time', None)
        if start is not None:
            ms = (time.perf_counter() - start) * 1000
            elapsed_ms = f'  {colors.stylize(f"{ms:.0f}ms", colors.DIM)}'
        print(f'  {code_str}  {colors.stylize(method.ljust(4), colors.DIM)}  {path}{elapsed_ms}')

    def run_wsgi(self):
        self._grow_start_time = time.perf_counter()
        return super().run_wsgi()


class PodServer:
    def __call__(self, environ, start_response):
        return self.wsgi_app(environ, start_response)

    def __init__(self, pod, host, port, debug=False):
        self.pod = pod
        self.host = host
        self.port = port
        self.pod.render_pool.pool_size = 1
        self.debug = debug
        self.routes = self.pod.router.routes

        # Trigger the dev handler hook.
        self.pod.extensions_controller.trigger(
            'dev_handler', self.routes, host=host, port=port, debug=debug
        )

        # Start off the server with a clean dependency graph.
        self.pod.podcache.dependency_graph.mark_clean()

    def dispatch_request(self, request):
        path = url_parse.unquote(request.path)  # Support escaped paths.
        matched = self.routes.match(path)

        if not matched:
            text = '{} was not found in routes.'
            raise errors.RouteNotFoundError(text.format(path))

        kind = matched.value.kind
        if kind == 'console':
            if 'handler' in matched.value.meta:
                handler_meta = None
                if 'meta' in matched.value.meta:
                    handler_meta = matched.value.meta['meta']
                return matched.value.meta['handler'](self.pod, request, matched, meta=handler_meta)
            return handlers.serve_console(self.pod, request, matched)
        return handlers.serve_pod(self.pod, request, matched)

    def wsgi_app(self, environ, start_response):
        try:
            request = handlers.Request(environ)
            response = self.dispatch_request(request)
            return response(environ, start_response)
        except Exception as e:
            request = handlers.Request(environ)
            response = handlers.serve_exception(self.pod, request, e)
            return response(environ, start_response)


def create_wsgi_app(pod, host, port, debug=False):
    podserver_app = PodServer(pod, host, port, debug=debug)
    assets_path = os.path.join(utils.get_grow_dir(), 'ui', 'admin', 'assets')
    ui_path = os.path.join(utils.get_grow_dir(), 'ui', 'dist')
    # pylint: disable=no-member
    return shared_data.SharedDataMiddleware(
        podserver_app,
        {
            '/_grow/ui': ui_path,
            '/_grow/assets': assets_path,
        },
    )
