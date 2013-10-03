from grow.common import config
from grow.pods import pods
from grow.pods import routes
from grow.pods import storage
from grow.server import pod_serving
from grow.server import podgroups
from grow.server import utils
import logging
import os
import webapp2


class BaseHandler(webapp2.RequestHandler):

  def respond_with_controller(self, controller):
    # TODO(jeremydw): Handle custom errors.
    if controller is None:
      return self.abort(404)

    # Update response headers with headers from controller.
    headers = controller.get_http_headers()
    self.response.headers.update(headers)

    # If a special token is in the response header indicating that the
    # file is going to be served from a different source, return now.
    if 'X-AppEngine-BlobKey' in self.response.headers:
      return

    try:
      return self.response.out.write(controller.render())
    except IOError as e:
      self.response.set_status(404)
      self.response.out.write('IOError: {}'.format(e))


class ConsoleHandler(BaseHandler):

  def get(self):
    pod = pods.Pod('pygrow/grow/growedit', storage=storage.FileStorage)
    controller = pod.match(self.request.path)
    self.respond_with_controller(controller)


class PodHandler(BaseHandler):

  def get(self):
    host = os.environ.get('HTTP_HOST', '')
    changeset = utils.get_changeset(host)

    # If on growspace.
    if (host in config.GROWSPACE_DOMAINS
        or os.environ.get('SERVER_SOFTWARE', '').startswith('Dev')):
      pod = pods.Pod('growspace/console', storage=storage.FileStorage)
      controller = pod.match(self.request.path)
      self.respond_with_controller(controller)
      return

    # If on a staging domain.
    elif changeset:
      domain = None
      podgroup = podgroups.Podgroup(config.PODS_DIR)
      podgroup.load_pods_by_id([changeset])

    # If in single-pod mode.
    elif 'grow:single_pod_root' in os.environ:
      domain = None
      root = os.path.dirname(os.environ['grow:single_pod_root'])
      podgroup = podgroups.Podgroup(root)
      pod_name = os.path.basename(os.path.normpath(os.environ['grow:single_pod_root']))
      podgroup.load_pods_by_id([pod_name])

    # Get the routing map from the "launched pods" podgroup.
    else:
      domain = os.environ.get('SERVER_NAME')
      try:
        podgroup = pod_serving.get_live_podgroup()
      # No routes ever deployed.
      except pod_serving.LiveRoutingMapNotFound:
        self.response.set_status(404)
        self.response.out.write('No routing map found.')
        return

    # Route issues a redirect.
    try:
      controller = podgroup.match(self.request.path, domain=domain)
    except routes.Errors.NotFound as e:
      controller = podgroup.match_error(self.request.path, domain=domain, status=404)
      self.response.set_status(404)
      if controller is not None:
        self.response.out.write(controller.render())
      return
    except routes.Errors.Redirect as e:
      self.response.set_status(301)
      self.response.headers['Location'] = e.new_url
      return

    # Resource just doesn't exist.
    if not controller:
      self.response.set_status(404)
      self.response.out.write('No matching route found.')
      return

    logging.debug('Matched URL to pod: %s', controller.pod)
    self.respond_with_controller(controller)


def set_single_pod_root(root):
  if root is None and 'grow:single_pod_root' in os.environ:
    del os.environ['grow:single_pod_root']
  if root is not None:
    os.environ['grow:single_pod_root'] = root
