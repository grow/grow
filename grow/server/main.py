"""Grow local development server."""

import os
from urllib import parse as url_parse
from werkzeug import serving
from werkzeug.middleware import shared_data
from grow.common import config
from grow.common import utils
from grow.pods import errors
from grow.server import handlers


# Use grow's logger instead of werkzeug's default.
class RequestHandler(serving.WSGIRequestHandler):

    @property
    def server_version(self):
        return 'Grow/{}'.format(config.VERSION)

    def log(self, *args, **kwargs):
        pass


class PodServer(object):

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
            'dev_handler', self.routes, host=host, port=port, debug=debug)

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
                return matched.value.meta['handler'](
                    self.pod, request, matched, meta=handler_meta)
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
    return shared_data.SharedDataMiddleware(podserver_app, {
        '/_grow/ui': ui_path,
        '/_grow/assets': assets_path,
    })
