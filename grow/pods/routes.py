"""
werkzeug routing:
  http://www.pocoo.org/~blackbird/wzdoc/routing.html
  http://werkzeug.pocoo.org/docs/routing/#werkzeug.routing.Map
"""

from . import messages
from . import locales
from .controllers import rendered
from .controllers import static
from grow.common import utils
import collections
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


class ValidationError(Error, ValueError):
  pass


class DuplicatePathsError(Error, ValueError):
  pass


class Routes(object):
  converters = {'grow': GrowConverter}

  def __init__(self, pod):
    self.pod = pod
    self._paths_to_locales_to_docs = collections.defaultdict(dict)
    self._routing_map = None

  def __iter__(self):
    return self.routing_map.iter_rules()

  def reset_cache(self, rebuild=True):
    if rebuild:
      self._build_routing_map()

  def get_doc(self, path, locale=None):
    if isinstance(locale, basestring):
      locale = locales.Locale(locale)
    return self._paths_to_locales_to_docs.get(path, {}).get(locale)

  def _build_routing_map(self):
    new_paths_to_locales_to_docs = collections.defaultdict(dict)
    rules = []
    # Content documents.
    for collection in self.pod.list_collections():
      for doc in collection.list_servable_documents(include_hidden=True):
        controller = rendered.RenderedController(
            view=doc.get_view(),
            document=doc,
            _pod=self.pod)
        rule = routing.Rule(doc.get_serving_path(), endpoint=controller)
        rules.append(rule)
        new_paths_to_locales_to_docs[doc.pod_path][doc.locale] = doc
    rules += self.list_static_routes()
    self._routing_map = routing.Map(rules, converters=Routes.converters)
    self._paths_to_locales_to_docs = new_paths_to_locales_to_docs
    return self._routing_map

  @property
  def routing_map(self):
    if not self.pod.env.cached or self._routing_map is None:
      return self._build_routing_map()
    return self._routing_map

  def list_static_routes(self):
    rules = []
    podspec = self.pod.get_podspec()
    podspec_config = podspec.get_config()
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
    return rules

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
    paths = set()
    for route in self:
      controller = route.endpoint
      new_paths = set(controller.list_concrete_paths())
      intersection = paths.intersection(new_paths)
      if intersection:
        text = '"{}" from {}'
        error = text.format(', '.join(intersection), controller)
        raise DuplicatePathsError(error)
      paths.update(new_paths)
    return list(paths)

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
