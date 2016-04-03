from ..pods import errors
from grow.common import utils
from grow.pods import storage
import jinja2
import logging
import os
import urllib
import webapp2
import webob
import werkzeug
from werkzeug import wrappers

_root = os.path.join(utils.get_grow_dir(), 'server', 'templates')
_loader = storage.FileStorage.JinjaLoader(_root)
_env = jinja2.Environment(
    loader=_loader,
    autoescape=True,
    trim_blocks=True,
    extensions=[
        'jinja2.ext.autoescape',
        'jinja2.ext.do',
        'jinja2.ext.i18n',
        'jinja2.ext.loopcontrols',
        'jinja2.ext.with_',
    ])


class BaseHandler(webapp2.RequestHandler):

    def handle_exception(self, exception, debug):
        pod = self.app.registry['pod']
        log_func = logging.exception if debug or not pod else pod.logger.error
        if isinstance(exception, webob.exc.HTTPException):
            status = exception.status_int
            log_func('{}: {}'.format(status, self.request.path))
        else:
            status = 500
            log_func('{}: {} - {}'.format(status, self.request.path, exception))
        kwargs = {
            'exception_type': str(type(exception)),
            'exception': exception,
            'pod': pod,
            'status': status,
        }
        if (isinstance(exception, errors.BuildError)):
            kwargs['build_error'] = exception.exception
        if (isinstance(exception, errors.BuildError)
           and isinstance(exception.exception, jinja2.TemplateSyntaxError)):
            kwargs['template_exception'] = exception.exception
        elif isinstance(exception, jinja2.TemplateSyntaxError):
            kwargs['template_exception'] = exception
        template = _env.get_template('error.html')
        html = template.render(kwargs)
        self.response.set_status(status)
        self.response.write(html)


def respond(pod, request):
    path = urllib.unquote(request.path)  # Support escaped paths.
    controller, params = pod.routes.match(path, request.environ)
    controller.validate(params)
    headers = controller.get_http_headers(params)
    content = controller.render(params)
    response = wrappers.Response(content)
    response.headers = headers
    if 'X-AppEngine-BlobKey' in response.headers:
        return
    return response


class BaseConsoleHandler(BaseHandler):

    def get(self, *args):
        pod = self.app.registry['pod']
        kwargs = {
            'pod': pod,
            'args': args,
        }
        template = _env.get_template(self.template_path)
        html = template.render(kwargs)
        self.response.write(html)


class CatalogHandler(BaseConsoleHandler):
    template_path = 'catalog.html'


class CatalogsHandler(BaseConsoleHandler):
    template_path = 'catalogs.html'


class CollectionsHandler(BaseConsoleHandler):
    template_path = 'collections.html'


class ConsoleHandler(BaseConsoleHandler):
    template_path = 'main.html'
