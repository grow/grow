from grow.common import utils
from grow.pods import env
from grow.pods import pods
from grow.pods import storage
import gflags as flags
import jinja2
import logging
import os
import webapp2
import webob
import werkzeug

FLAGS = flags.FLAGS

flags.DEFINE_boolean(
    'debug', False, 'Whether to show debug output.')

_root = os.path.join(utils.get_grow_dir(), 'server', 'templates')
_loader = storage.FileStorage.JinjaLoader(_root)
_env = jinja2.Environment(loader=_loader, autoescape=True, trim_blocks=True,
                          extensions=['jinja2.ext.i18n'])


def set_pod_root(root):
  if root is None and 'grow:pod_root' in os.environ:
    del os.environ['grow:pod_root']
  if root is not None:
    os.environ['grow:pod_root'] = root


class BaseHandler(webapp2.RequestHandler):

  def handle_exception(self, exception, debug):
    if FLAGS.debug:
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
    try:
      root = os.environ['grow:pod_root']
    except KeyError:
      raise Exception('Environment variable "grow:pod_root" missing.')
    environment = env.Env.from_wsgi_env(self.request.environ)
    pod = pods.Pod(root, env=environment)
    try:
      controller = pod.routes.match(self.request.path, self.request.environ)
      self.respond_with_controller(controller)
    except werkzeug.routing.RequestRedirect as e:
      self.redirect(e.new_url)
