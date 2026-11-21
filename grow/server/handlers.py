"""Response handlers for dev server."""

import logging
import mimetypes
import os
import re
import sys
import traceback

import jinja2
import webob

# NOTE: exc imported directly, webob.exc doesn't work when frozen.
from webob import exc as webob_exc
from werkzeug import wrappers
from werkzeug.exceptions import NotFound

from grow.pods import errors, ui


class Request(webob.Request):
    pass


class Response(webob.Response):
    default_conditional_response = True


def serve_console(pod, _request, _matched, **_kwargs):
    """Serve the default console page."""
    kwargs = {'pod': pod}
    env = ui.create_jinja_env()
    template = env.get_template('/views/base.html')
    content = template.render(kwargs)
    response = wrappers.Response(content)
    response.headers['Content-Type'] = 'text/html'
    return response


def serve_exception(pod, request, exc, **_kwargs):
    """Serve the exception page."""
    if isinstance(exc, webob_exc.HTTPException):
        status = exc.status_int
        logging.exception(f'{status}: {request.path}')
    elif isinstance(exc, errors.RouteNotFoundError) or isinstance(exc, NotFound):
        status = 404
        logging.error(f'{status}: {request.path}')
    else:
        status = 500
        logging.exception(f'{status}: {request.path} - {exc}')
    env = ui.create_jinja_env()
    template = env.get_template('/views/error.html')
    if (isinstance(exc, errors.BuildError)):
        t_back = exc.traceback
    else:
        unused_error_type, unused_value, t_back = sys.exc_info()
    formatted_traceback = [
        re.sub('^  ', '', line)
        for line in traceback.format_tb(t_back)]
    formatted_traceback = '\n'.join(formatted_traceback)
    kwargs = {
        'exception': exc,
        'is_web_exception': isinstance(exc, webob_exc.HTTPException),
        'pod': pod,
        'status': status,
        'traceback': formatted_traceback,
    }
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


def serve_pod(pod, request, matched, **_kwargs):
    """Serve pod contents using the routing."""
    controller = pod.router.get_render_controller(
        request.path, matched.value, params=matched.params)
    response = None
    headers = controller.get_http_headers()
    jinja_env = pod.render_pool.get_jinja_env(
        controller.doc.locale) if controller.use_jinja else None
    rendered_document = controller.render(jinja_env=jinja_env, request=request)
    content = rendered_document.read()
    response = Response(body=content)
    response.headers.update(headers)

    if pod.podcache.is_dirty:
        pod.podcache.write()

    return response


def serve_ui_tool(pod, _request, values, **_kwargs):
    tool = values.get('tool') or ''
    node_modules_root = os.path.realpath(os.path.join(pod.root, 'node_modules'))
    resolved_path = os.path.realpath(os.path.join(node_modules_root, tool))
    if os.path.commonpath([node_modules_root, resolved_path]) != node_modules_root:
        raise NotFound()
    tool_path = f'node_modules/{tool}'
    response = wrappers.Response(pod.read_file(tool_path))
    guessed_type = mimetypes.guess_type(tool_path)
    mime_type = guessed_type[0] or 'text/plain'
    response.headers['Content-Type'] = mime_type
    return response


def serve_run_preprocessor(pod, _request, values):
    name = values.get('name')
    if name:
        pod.preprocess([name])
        out = f'Finished preprocessor run -> {name}'
    else:
        out = 'No preprocessor found.'
    response = wrappers.Response(out)
    response.headers['Content-Type'] = 'text/plain'
    return response
