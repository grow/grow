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
    if debug:
      logging.exception(exception)
    else:
      logging.error(str(exception))
    template = _env.get_template('error.html')
    html = template.render({'error': {'title': str(exception)}})
    if isinstance(exception, webob.exc.HTTPException):
      self.response.set_status(exception.code)
    else:
      self.response.set_status(500)
    self.response.write(html)

  def respond_with_controller(self, controller):
    headers = controller.get_http_headers()
    self.response.headers.update(headers)
    if 'X-AppEngine-BlobKey' in self.response.headers:
      return
    return self.response.out.write(controller.render())


class PodHandler(BaseHandler):

  def get(self):
    pod = self.app.registry['pod']
    try:
      controller = pod.routes.match(self.request.path, self.request.environ)
      self.respond_with_controller(controller)
    except werkzeug.routing.RequestRedirect as e:
      self.redirect(e.new_url)
