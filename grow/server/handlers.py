from ..pods import errors
from grow.common import utils
from grow.pods import storage
import jinja2
import logging
import os
import webapp2
import webob
import werkzeug

_root = os.path.join(utils.get_grow_dir(), 'server', 'templates')
_loader = storage.FileStorage.JinjaLoader(_root)
_env = jinja2.Environment(loader=_loader, autoescape=True, trim_blocks=True,
                          extensions=['jinja2.ext.i18n'])


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


class PodHandler(BaseHandler):

  def get(self):
    pod = self.app.registry['pod']
    try:
      controller = pod.routes.match(self.request.path, self.request.environ)
      controller.validate()
      headers = controller.get_http_headers()
      self.response.headers.update(headers)
      if 'X-AppEngine-BlobKey' in self.response.headers:
        return
      self.response.out.write(controller.render())
    except werkzeug.routing.RequestRedirect as e:
      self.redirect(e.new_url)


class ConsoleHandler(BaseHandler):

  def get(self):
    pod = self.app.registry['pod']
    kwargs = {
        'pod': pod,
    }
    template = _env.get_template('main.html')
    html = template.render(kwargs)
    self.response.write(html)
