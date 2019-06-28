"""Response handlers for dev server."""

import mimetypes
import webob
from werkzeug import wrappers
from grow.pods import ui


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


def serve_editor(pod, _request, matched, meta=None, **_kwargs):
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


def serve_pod(pod, request, matched, **_kwargs):
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
