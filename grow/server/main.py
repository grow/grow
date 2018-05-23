"""Grow local development server."""

import logging
import mimetypes
import os
import re
import sys
import traceback
import urllib
import jinja2
import webob
# NOTE: exc imported directly, webob.exc doesn't work when frozen.
from webob import exc as webob_exc
from werkzeug import routing
from werkzeug import utils as werkzeug_utils
from werkzeug import wrappers
from werkzeug import serving
from werkzeug import wsgi
from grow.common import config
from grow.common import utils
from grow.routing import router
from grow.pods import errors
from grow.pods import ui
from grow.server import api


class Request(wrappers.BaseRequest):
    pass


class ReRouteRequest(webob.Request):
    pass


class Response(webob.Response):
    default_conditional_response = True


# Use grow's logger instead of werkzeug's default.
class RequestHandler(serving.WSGIRequestHandler):

    @property
    def server_version(self):
        return 'Grow/{}'.format(config.VERSION)

    def log(self, *args, **kwargs):
        pass


def serve_console(pod, request, values):
    kwargs = {'pod': pod}
    values_to_templates = {
        'content': 'collections.html',
        'preprocessors': 'preprocessors.html',
        'translations': 'catalogs.html',
    }
    value = values.get('page')
    template_path = values_to_templates.get(value, 'main.html')
    if value == 'translations' and values.get('locale'):
        kwargs['locale'] = values.get('locale')
        template_path = 'catalog.html'
    env = ui.create_jinja_env()
    template = env.get_template('/views/{}'.format(template_path))
    content = template.render(kwargs)
    response = wrappers.Response(content)
    response.headers['Content-Type'] = 'text/html'
    return response


def serve_console_reroute(pod, _request, _matched, **_kwargs):
    """Serve the default console page."""
    kwargs = {'pod': pod}
    env = ui.create_jinja_env()
    template = env.get_template('/views/base-reroute.html')
    content = template.render(kwargs)
    response = wrappers.Response(content)
    response.headers['Content-Type'] = 'text/html'
    return response


def serve_editor_reroute(pod, _request, matched, meta=None, **_kwargs):
    """Serve the default console page."""
    kwargs = {
        'pod': pod,
        'meta': meta,
        'path': matched.params['path'] if 'path' in matched.params else '',
    }
    env = ui.create_jinja_env()
    template = env.get_template('/views/editor.html')
    content = template.render(kwargs)
    response = wrappers.Response(content)
    response.headers['Content-Type'] = 'text/html'
    return response


def serve_pod(pod, request, values):
    path = urllib.unquote(request.path)  # Support escaped paths.
    controller, params = pod.routes.match(path, request.environ)
    controller.validate(params)
    headers = controller.get_http_headers(params)
    if 'X-AppEngine-BlobKey' in headers:
        return Response(headers=headers)
    content = controller.render(params)
    response = Response(body=content)
    response.headers.update(headers)

    if pod.podcache.is_dirty:
        pod.podcache.write()

    return response


def serve_pod_reroute(pod, request, matched, **_kwargs):
    """Serve pod contents using the new routing."""
    controller = pod.router.get_render_controller(
        request.path, matched.value, params=matched.params)
    response = None
    headers = controller.get_http_headers()
    if 'X-AppEngine-BlobKey' in headers:
        return Response(headers=headers)
    jinja_env = pod.render_pool.get_jinja_env(
        controller.doc.locale) if controller.use_jinja else None
    rendered_document = controller.render(jinja_env=jinja_env)
    content = rendered_document.read()
    response = Response(body=content)
    response.headers.update(headers)

    if pod.podcache.is_dirty:
        pod.podcache.write()

    return response


def serve_ui_tool(pod, request, values):
    tool_path = 'node_modules/{}'.format(values.get('tool'))
    response = wrappers.Response(pod.read_file(tool_path))
    guessed_type = mimetypes.guess_type(tool_path)
    mime_type = guessed_type[0] or 'text/plain'
    response.headers['Content-Type'] = mime_type
    return response


def serve_ui_tool_reroute(pod, request, values, **_kwargs):
    tool_path = 'node_modules/{}'.format(values.get('tool'))
    response = wrappers.Response(pod.read_file(tool_path))
    guessed_type = mimetypes.guess_type(tool_path)
    mime_type = guessed_type[0] or 'text/plain'
    response.headers['Content-Type'] = mime_type
    return response


def serve_run_preprocessor(pod, request, values):
    name = values.get('name')
    if name:
        pod.preprocess([name])
        out = 'Finished preprocessor run -> {}'.format(name)
    else:
        out = 'No preprocessor found.'
    response = wrappers.Response(out)
    response.headers['Content-Type'] = 'text/plain'
    return response


class PodServer(object):

    def __init__(self, pod, debug=False):
        logging.warn(
            'WARNING: Using old routing. '
            'The old routing will be removed in a future version. '
            'Please file issues on GitHub if you are having issues with the new routing.')

        rule = routing.Rule
        self.pod = pod
        self.debug = debug
        self.url_map = routing.Map([
            rule('/', endpoint=serve_pod),
            rule('/_grow/ui/tools/<path:tool>', endpoint=serve_ui_tool),
            rule('/_grow/preprocessors/run/<path:name>',
                 endpoint=serve_run_preprocessor),
            rule('/_grow/<any("translations"):page>/<path:locale>',
                 endpoint=serve_console),
            rule('/_grow/<path:page>', endpoint=serve_console),
            rule('/_grow', endpoint=serve_console),
            rule('/<path:path>', endpoint=serve_pod),
        ], strict_slashes=False)

        # Start off the server with a clean dependency graph.
        self.pod.podcache.dependency_graph.mark_clean()

    def dispatch_request(self, request):
        adapter = self.url_map.bind_to_environ(request.environ)
        try:
            endpoint, values = adapter.match()
            return endpoint(self.pod, request, values)
        except routing.RequestRedirect as e:
            return werkzeug_utils.redirect(e.new_url)

    def wsgi_app(self, environ, start_response):
        request = Request(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)

    def __call__(self, environ, start_response):
        try:
            return self.wsgi_app(environ, start_response)
        except Exception as e:
            request = Request(environ)
            response = self.handle_exception(request, e)
            return response(environ, start_response)

    def handle_exception(self, request, exc):
        self.debug = True
        log = logging.exception if self.debug else self.pod.logger.error
        if isinstance(exc, webob_exc.HTTPException):
            status = exc.status_int
            log('{}: {}'.format(status, request.path))
        elif isinstance(exc, errors.RouteNotFoundError):
            status = 404
            log('{}: {}'.format(status, request.path))
        else:
            status = 500
            log('{}: {} - {}'.format(status, request.path, exc))
        env = ui.create_jinja_env()
        template = env.get_template('/views/error.html')
        if (isinstance(exc, errors.BuildError)):
            tb = exc.traceback
        else:
            unused_error_type, unused_value, tb = sys.exc_info()
        formatted_traceback = [
            re.sub('^  ', '', line)
            for line in traceback.format_tb(tb)]
        formatted_traceback = '\n'.join(formatted_traceback)
        kwargs = {
            'exception': exc,
            'is_web_exception': isinstance(exc, webob_exc.HTTPException),
            'pod': self.pod,
            'status': status,
            'traceback': formatted_traceback,
        }
        try:
            home_doc = self.pod.get_home_doc()
            if home_doc:
                kwargs['home_url'] = home_doc.url.path
        except:
            pass
        if (isinstance(exc, errors.BuildError)):
            kwargs['build_error'] = exc.exception
        if (isinstance(exc, errors.BuildError)
                and isinstance(exc.exception, jinja2.TemplateSyntaxError)):
            kwargs['template_exception'] = exc.exception
        elif isinstance(exc, jinja2.TemplateSyntaxError):
            kwargs['template_exception'] = exc
        content = template.render(**kwargs)
        response = wrappers.Response(content, status=status)
        response.headers['Content-Type'] = 'text/html'
        return response


class PodServerReRoute(PodServer):

    def __init__(self, pod, host, port, debug=False):
        logging.warn(
            'NOTICE: Using new routing, use --old-routing to use the older routing.')

        self.pod = pod
        self.host = host
        self.port = port
        self.pod.render_pool.pool_size = 1
        self.debug = debug
        self.routes = self.pod.router.routes

        self.routes.add('/_grow/ui/tools/:tool', router.RouteInfo('console', {
            'handler': serve_ui_tool_reroute,
        }))
        editor_meta = {
            'handler': serve_editor_reroute,
            'meta': {
                'app': self,
            },
        }
        self.routes.add('/_grow/editor/*path',
                        router.RouteInfo('console', editor_meta))
        self.routes.add('/_grow/editor',
                        router.RouteInfo('console', editor_meta))
        self.routes.add('/_grow/api/*path', router.RouteInfo('console', {
            'handler': api.serve_api,
        }))
        self.routes.add('/_grow', router.RouteInfo('console', {
            'handler': serve_console_reroute,
        }))

        # Trigger the dev handler hook.
        self.pod.extensions_controller.trigger(
            'dev_handler', self.routes, debug=debug)

        # Start off the server with a clean dependency graph.
        self.pod.podcache.dependency_graph.mark_clean()

    def dispatch_request(self, request):
        path = urllib.unquote(request.path)  # Support escaped paths.
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
            return serve_console_reroute(self.pod, request, matched)
        return serve_pod_reroute(self.pod, request, matched)

    def wsgi_app(self, environ, start_response):
        request = ReRouteRequest(environ)
        response = self.dispatch_request(request)
        return response(environ, start_response)


def create_wsgi_app(pod, host, port, debug=False):
    if pod.use_reroute:
        podserver_app = PodServerReRoute(pod, host, port, debug=debug)
    else:
        podserver_app = PodServer(pod, debug=debug)
    assets_path = os.path.join(utils.get_grow_dir(), 'ui', 'admin', 'assets')
    ui_path = os.path.join(utils.get_grow_dir(), 'ui', 'dist')
    return wsgi.SharedDataMiddleware(podserver_app, {
        '/_grow/ui': ui_path,
        '/_grow/assets': assets_path,
    })
