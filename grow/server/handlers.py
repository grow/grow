"""Response handlers for dev server."""

import logging
import mimetypes
import re
import sys
import traceback
import jinja2
import webob
# NOTE: exc imported directly, webob.exc doesn't work when frozen.
from webob import exc as webob_exc
from werkzeug import wrappers
from werkzeug.exceptions import NotFound
from grow.documents import document
from grow.pods import errors
from grow.pods import ui


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
    debug = True
    logging.exception
    if isinstance(exc, webob_exc.HTTPException):
        status = exc.status_int
        logging.exception('{}: {}'.format(status, request.path))
    elif isinstance(exc, errors.RouteNotFoundError):
        status = 404
        logging.error('{}: {}'.format(status, request.path))
    elif isinstance(exc, NotFound):
        status = 404
        logging.error('{}: {}'.format(status, request.path))
    else:
        status = 500
        logging.exception('{}: {} - {}'.format(status, request.path, exc))
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
    home_doc = pod.get_home_doc()
    if home_doc and home_doc.exists:
        kwargs['home_url'] = home_doc.url.path
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
    tool_path = 'node_modules/{}'.format(values.get('tool'))
    response = wrappers.Response(pod.read_file(tool_path))
    guessed_type = mimetypes.guess_type(tool_path)
    mime_type = guessed_type[0] or 'text/plain'
    response.headers['Content-Type'] = mime_type
    return response


def serve_run_preprocessor(pod, _request, values):
    name = values.get('name')
    if name:
        pod.preprocess([name])
        out = 'Finished preprocessor run -> {}'.format(name)
    else:
        out = 'No preprocessor found.'
    response = wrappers.Response(out)
    response.headers['Content-Type'] = 'text/plain'
    return response
