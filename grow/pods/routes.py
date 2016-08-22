from . import locales
from . import messages
from . import rendered
from . import sitemap
from . import static
from grow.common import utils
from werkzeug.contrib import cache
from werkzeug import routing
import collections
import os
import webob
import werkzeug


class Error(Exception):
    pass


class GrowConverter(routing.PathConverter):
    pass


class DuplicatePathsError(Error, ValueError):
    pass


class Routes(object):
    converters = {'grow': GrowConverter}

    def __init__(self, pod):
        self.pod = pod
        self.cache = pod.cache
        self._routing_map = None
        self._static_routing_map = None

    def __iter__(self):
        return self.routing_map.iter_rules()

    @property
    def podspec(self):
        return self.pod.get_podspec().get_config()

    def reset_cache(self, rebuild=True, inject=False):
        self.cache.delete('routes')
        if rebuild:
            self._build_routing_map(inject=False)

    @property
    def routing_map(self):
        return self._build_routing_map()

    def _build_routing_map(self, inject=False):
        rules = self.cache.get('routes')
        if rules is None:
            rules = []
            serving_paths = set()
            # Content documents.
            for collection in self.pod.list_collections():
                for route in collection.routes():
                    rule = routing.Rule(route.path_format, endpoint=route)
                    rules.append(rule)
            # Static routes.
            rules += self._build_static_routing_map_and_return_rules()
#            self.cache.set('routes', rules)
        return routing.Map(rules, converters=Routes.converters)

#                if serving_path in serving_paths:
#                    text = 'Serving path "{}" was used twice by {}'
#                    raise DuplicatePathsError(text.format(serving_path, doc))
#                serving_paths.add(serving_path)
#                rule = routing.Rule(serving_path, endpoint=controller)

    def _build_static_routing_map_and_return_rules(self):
        rules = self.list_static_routes()
        self._static_routing_map = routing.Map(rules, converters=Routes.converters)
        return [rule.empty() for rule in rules]

    @property
    def static_routing_map(self):
        if self._static_routing_map is None:
            self._build_static_routing_map_and_return_rules()
        return self._static_routing_map

    def format_path(self, path):
        path = '' if path is None else path
        if 'root' in self.podspec:
            path = path.replace('{root}', self.podspec['root'])
        path = path.replace('{env.fingerprint}', self.pod.env.fingerprint)
        path = path.replace('{fingerprint}', '<grow:fingerprint>')
        path = path.replace('//', '/')
        return path

    def list_static_routes(self):
        rules = []
        # Auto-generated from flags.
        if 'sitemap' in self.podspec:
            sitemap_path = self.podspec['sitemap'].get('path', '/sitemap.xml')
            path_format = utils.reformat_rule(sitemap_path, pod=self.pod)
            route = messages.SitemapRoute(path_format=path_format)
            rules.append(routing.Rule(route.path_format, endpoint=route))
        if 'static_dir' in self.pod.flags:
            path = self.pod.flags['static_dir'] + '<grow:filename>'
            route = messages.StaticRoute(
                path_format=path,
                pod_path_format=path)
            rules.append(routing.Rule(route.path_format, endpoint=route))
        if 'static_dirs' in self.podspec:
            for config in self.podspec['static_dirs']:
                if config.get('dev') and not self.pod.env.dev:
                    continue
                static_dir = config['static_dir'] + '<grow:filename>'
                serve_at = config['serve_at'] + '<grow:filename>'
                serve_at = self.format_path(serve_at)
                localization = config.get('localization')
                fingerprinted = config.get('fingerprinted', False)
                if localization:
                    localization = messages.StaticLocalization(
                        static_dir=localization.get('static_dir'),
                        serve_at=localization.get('serve_at'))
                route = messages.StaticRoute(
                    path_format=serve_at,
                    pod_path_format=static_dir,
                    localized=False,
                    localization=localization,
                    fingerprinted=fingerprinted)
                rules.append(routing.Rule(route.path_format, endpoint=route))
                if localization:
                    localized_serve_at = localization.serve_at \
                        + '<grow:filename>'
                    static_dir = localization.static_dir
                    localized_static_dir = static_dir + '<grow:filename>'
                    rule_path = utils.reformat_rule(
                        localized_serve_at, pod=self.pod)
                    route = messages.StaticRoute(
                        path_format=localized_serve_at,
                        pod_path_format=localized_static_dir,
                        localized=True,
                        localization=localization,
                        fingerprinted=fingerprinted)
                    rules.append(routing.Rule(rule_path, endpoint=route))
        return rules

    def match(self, path, env):
        """Matches a controller from the pod.

        Returns:
          Controller matching request.
        Raises:
          routing.RequestRedirect: When the controller is a redirect.
          routing.NotFound: When no controller is found.
        """
        if '/..' in path:
            raise webob.exc.HTTPBadRequest('Invalid path.')
        urls = self.routing_map.bind_to_environ(env)
        try:
            endpoint, params = urls.match(path)
            controller = self.route_to_controller(endpoint, params)
            return controller, params
        except routing.NotFound:
            for r in self:
                print r
            raise webob.exc.HTTPNotFound('{} not found.'.format(path))

    def match_error(self, path, status=404):
        if status == 404 and self.pod.error_routes:
            view = self.pod.error_routes.get('default')
            return rendered.RenderedController(view=view, _pod=self.pod)

    def get_locales_to_paths(self):
        locales_to_paths = collections.defaultdict(list)
        for route in self:
            controller = self.route_to_controller(route.endpoint)
            paths = controller.list_concrete_paths()
            locale = controller.locale
            locales_to_paths[locale] += paths
        return locales_to_paths

    def get_controllers_to_paths(self):
        controllers_to_paths = collections.defaultdict(list)
        for route in self:
            controller = self.route_to_controller(route.endpoint)
            name = str(controller)
            paths = controller.list_concrete_paths()
            controllers_to_paths[name] += paths
            controllers_to_paths[name].sort()
        return controllers_to_paths

    @utils.memoize
    def list_concrete_paths(self):
        paths = set()
        for route in self:
            controller = self.route_to_controller(route.endpoint)
            new_paths = set(controller.list_concrete_paths())
            paths.update(new_paths)
        return list(paths)

    def route_to_controller(self, route_message, params=None):
        params = params or {}
        if isinstance(route_message, messages.Route):
            pod_path = route_message.pod_path
            locale = locales.Locale.from_alias(self.pod, params.get('locale'))
            doc = self.pod.get_doc(pod_path, locale=locale)
            return rendered.RenderedController(doc=doc, _pod=self.pod)
        elif isinstance(route_message, messages.SitemapRoute):
            path_format = route_message.path_format
            path_format = utils.reformat_rule(path_format, pod=self.pod)
            return sitemap.SitemapController(
                pod=self.pod,
                path=path_format,
                collections=self.podspec['sitemap'].get('collections'),
                locales=self.podspec['sitemap'].get('locales'))
        else:
            return static.StaticController(
                path_format=route_message.path_format,
                source_format=route_message.pod_path_format,
                fingerprinted=route_message.fingerprinted,
                localization=route_message.localization,
                localized=route_message.localized,
                pod=self.pod)
