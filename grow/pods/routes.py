"""
werkzeug routing:
  http://www.pocoo.org/~blackbird/wzdoc/routing.html
  http://werkzeug.pocoo.org/docs/routing/#werkzeug.routing.Map
"""

from grow.common import utils
from grow.pods import controllers
from grow.pods import messages
from werkzeug import routing
from werkzeug import exceptions


class Errors(object):
  NotFound = exceptions.NotFound
  Redirect = routing.RequestRedirect


class GrowConverter(routing.PathConverter):
  pass


class Routes(object):
  converters = {'grow': GrowConverter}

  def __init__(self, pod):
    self.pod = pod

  @property
  def domains(self):
    return self.pod.yaml.get('domains')

  @property
  @utils.memoize
  def routing_map(self):
    rules = []

    # Content documents.
    for collection in self.pod.list_collections():
      for doc in collection.list_servable_documents(include_hidden=True):
        controller = controllers.PageController(
            view=doc.get_view(),
            document=doc,
            _pod=self.pod)
        rule = routing.Rule(doc.get_serving_path(), endpoint=controller)
        rules.append(rule)

    # Extra routes.
    extra_routes = self.pod.yaml.get('routes', [])
    for route in extra_routes:
      if route['kind'] == 'static':
        controller = controllers.StaticController(
            path_format=route['path'], source_format=route['source'], pod=self.pod)
        rules.append(routing.Rule(route['path'], endpoint=controller))
      elif route['kind'] == 'page':
        controller = controllers.PageController(
            view=route['view'], path=route['path'], _pod=self.pod)
        rules.append(routing.Rule(route['path'], endpoint=controller))

    # Auto-generated from flags.
    if 'static_dir' in self.pod.flags:
      path = self.pod.flags['static_dir'] + '<grow:filename>'
      controller = controllers.StaticController(path_format=path, source_format=path, pod=self.pod)
      rules.append(routing.Rule(path, endpoint=controller))

    routing_map = routing.Map(rules, converters=Routes.converters)
    return routing_map

  def match(self, path, domain=None, script_name=None, subdomain=None, url_scheme=None):
    """Matches a controller from the pod.

    Returns:
      Controller matching request.
    Raises:
      routing.RequestRedirect: When the controller is a redirect.
      routing.NotFound: When no controller is found.
    """
    if url_scheme is None:
      url_scheme = 'http'
    if domain is None:  # Needed for generating static files.
      domain = 'localhost'
    urls = self.routing_map.bind(domain, script_name, subdomain, url_scheme)
    controller, route_params = urls.match(path)
    controller.set_route_params(route_params)
#    controller.validate_route_params(route_params)
    # validate route_params here, raise NotFound if params are invalid
    return controller

  def match_error(self, path, domain=None, status=404):
    if status == 404 and self.pod.error_routes:
      view = self.pod.error_routes.get('default')
      return controllers.PageController(view=view, pod=self.pod)

  def list_concrete_paths(self):
    path_formats = []
    for route in self.routing_map.iter_rules():
      controller = route.endpoint
      path_formats.extend(controller.list_concrete_paths())
    return path_formats

  def to_message(self):
    message = messages.RoutesMessage()
    if self.domains:
      message.domains = self.domains
    message.routes = []
    for path in self.list_concrete_paths():
      route_message = messages.RouteMessage()
      route_message.path = path
      message.routes.append(route_message)
    return message
