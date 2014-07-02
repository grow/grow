"""
werkzeug routing:
  http://www.pocoo.org/~blackbird/wzdoc/routing.html
  http://werkzeug.pocoo.org/docs/routing/#werkzeug.routing.Map
"""

from . import messages
from .controllers import rendered
from .controllers import static
from grow.common import utils
import texttable
import logging
import webob
import werkzeug


routing = werkzeug.routing


class Error(Exception):
  pass


class Errors(object):
  Redirect = routing.RequestRedirect


class GrowConverter(routing.PathConverter):
  pass


class Routes(object):
  converters = {'grow': GrowConverter}

  def __init__(self, pod):
    self.pod = pod

  def __iter__(self):
    return self.routing_map.iter_rules()

  @property
  @utils.memoize
  def routing_map(self):
    rules = []
    podspec = self.pod.get_podspec()
    podspec_config = podspec.get_config()

    # Content documents.
    for collection in self.pod.list_collections():
      for doc in collection.list_servable_documents(include_hidden=True):
        controller = rendered.RenderedController(
            view=doc.get_view(),
            document=doc,
            _pod=self.pod)
        rule = routing.Rule(doc.get_serving_path(), endpoint=controller)
        rules.append(rule)

    # Auto-generated from flags.
    if 'static_dir' in self.pod.flags:
      path = self.pod.flags['static_dir'] + '<grow:filename>'
      controller = static.StaticController(
          path_format=path, source_format=path, pod=self.pod)
      rules.append(routing.Rule(path, endpoint=controller))

    if 'static_dirs' in podspec_config:
      for config in podspec_config['static_dirs']:
        static_dir = config['static_dir'] + '<grow:filename>'
        serve_at = config['serve_at'] + '<grow:filename>'
        controller = static.StaticController(path_format=serve_at,
                                             source_format=static_dir,
                                             pod=self.pod)
        rules.append(routing.Rule(serve_at, endpoint=controller))

    routing_map = routing.Map(rules, converters=Routes.converters)
    return routing_map

  def match(self, path, env):
    """Matches a controller from the pod.

    Returns:
      Controller matching request.
    Raises:
      routing.RequestRedirect: When the controller is a redirect.
      routing.NotFound: When no controller is found.
    """
    urls = self.routing_map.bind_to_environ(env)
    try:
      controller, route_params = urls.match(path)
      controller.set_route_params(route_params)
      # validate route_params here, raise NotFound if params are invalid
      # controller.validate_route_params(route_params)
      return controller
    except routing.NotFound:
      raise webob.exc.HTTPNotFound()

  def match_error(self, path, status=404):
    if status == 404 and self.pod.error_routes:
      view = self.pod.error_routes.get('default')
      return rendered.RenderedController(view=view, _pod=self.pod)

  @utils.memoize
  def list_concrete_paths(self):
    path_formats = []
    for route in self.routing_map.iter_rules():
      controller = route.endpoint
      path_formats.extend(controller.list_concrete_paths())
    return path_formats

  def to_message(self):
    message = messages.RoutesMessage()
    message.routes = []
    for route in self:
      controller = route.endpoint
      message.routes.extend(controller.to_route_messages())
    return message

  def pretty_print(self):
    table = texttable.Texttable(max_width=0)
    table.set_deco(texttable.Texttable.HEADER)
    rows = []
    rows.append(['Kind', 'Path'])
    for route in self:
      controller = route.endpoint
      for path in controller.list_concrete_paths():
        rows.append([controller.KIND, path])
    table.add_rows(rows)
    logging.info('\n' + table.draw() + '\n')
