from grow.common import utils
from grow.pods import storage
from grow.server import podgroups
import jinja2
import logging
import os
import webapp2
import webob

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
    template = _env.get_template('error.html')
    html = template.render({'error': {'title': str(exception)}})
    if isinstance(exception, webob.exc.HTTPException):
      self.response.set_status(exception.code)
    else:
      self.response.set_status(500)
      logging.exception(exception)
    self.response.write(html)

  def respond_with_controller(self, controller):
    headers = controller.get_http_headers()
    self.response.headers.update(headers)
    if 'X-AppEngine-BlobKey' in self.response.headers:
      return
    return self.response.out.write(controller.render())


class PodHandler(BaseHandler):

  def get(self):
    if 'grow:pod_root' not in os.environ:
      raise Exception('Environment variable "grow:pod_root" missing.')
    domain = self.request.host
    url_scheme = self.request.scheme
    root = os.path.dirname(os.environ['grow:pod_root'])
    podgroup = podgroups.Podgroup(root)
    pod_name = os.path.basename(os.path.normpath(os.environ['grow:pod_root']))
    podgroup.load_pods_by_id([pod_name])
    controller = podgroup.match(self.request.path, domain=domain, url_scheme=url_scheme)
    self.respond_with_controller(controller)
