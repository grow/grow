"""
werkzeug routing:
  http://www.pocoo.org/~blackbird/wzdoc/routing.html
  http://werkzeug.pocoo.org/docs/routing/#werkzeug.routing.Map
"""

from grow.common import utils
from grow.pods import errors
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
    for blueprint in self.pod.list_blueprints():
      for doc in blueprint.list_servable_documents():
        controller = controllers.PageController(view=doc.get_view(), document=doc, pod=self.pod)
        rule = routing.Rule(doc.get_serving_path(), endpoint=controller)
        rules.append(rule)

    # Extra routes.
    extra_routes = self.pod.yaml.get('routes', [])
    for route in extra_routes:
      if route['kind'] == 'static':
        controller = controllers.StaticController(path_format=route['path'], source_format=route['source'], pod=self.pod)
        rules.append(routing.Rule(route['path'], endpoint=controller))

    # Auto-generated from flags.
    if 'public_dir' in self.pod.flags:
      path = self.pod.flags['public_dir'] + '<grow:filename>'
      controller = controllers.StaticController(path_format=path, source_format=path, pod=self.pod)
      rules.append(routing.Rule(path, endpoint=controller))

    return routing.Map(rules, converters=Routes.converters)

  def match(self, path, domain=None, script_name=None, subdomain=None, url_scheme='http'):
    """Matches a controller from the pod.

    Returns:
      Controller matching request.
    Raises:
      routing.RequestRedirect: When the controller is a redirect.
      routing.NotFound: When no controller is found.
    """
    if domain and not self.domains:
      message = 'A domain was specified but routes are not bound to a domain.'
      raise errors.RouteNotFoundError(message)

    if domain and self.domains and domain not in self.domains:
      message = 'Routes not bound to domain "{}".'.format(domain)
      raise errors.RouteNotFoundError(message)

    domain = 'localhost' if domain is None else domain
    urls = self.routing_map.bind(domain, script_name, subdomain, url_scheme)

    controller, route_params = urls.match(path)
    controller.set_route_params(route_params)
    return controller

  def match_error(self, path, domain=None, status=404):
    if status == 404 and 'error_404' in self.pod.flags:
      view = self.pod.flags.get('error_404')
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
    return message
