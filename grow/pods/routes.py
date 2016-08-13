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

    def _build_routing_map(self, inject=False):
        rules = []
        serving_paths = set()
        # Content documents.
        for collection in self.pod.list_collections():
#            for doc in collection.list_servable_documents(include_hidden=True, inject=inject):
#                controller = rendered.RenderedController(
#                    view=doc.view, doc=doc, _pod=self.pod)
#                serving_path = doc.get_serving_path()
#                if serving_path in serving_paths:
#                    text = 'Serving path "{}" was used twice by {}'
#                    raise DuplicatePathsError(text.format(serving_path, doc))
#                serving_paths.add(serving_path)
#                rule = routing.Rule(serving_path, endpoint=controller)
            for route in collection.routes():
                rule = routing.Rule(route.path_format, endpoint=route)
                rules.append(rule)
        # Static routes.
        rules += self._build_static_routing_map_and_return_rules()
        return routing.Map(rules, converters=Routes.converters)

    def _build_static_routing_map_and_return_rules(self):
        rules = self.list_static_routes()
        self._static_routing_map = routing.Map(rules, converters=Routes.converters)
        return [rule.empty() for rule in rules]

    @property
    def static_routing_map(self):
        if self._static_routing_map is None:
            self._build_static_routing_map_and_return_rules()
        return self._static_routing_map

    @property
    def routing_map(self):
        routing_map = self.cache.get('routes')
        if routing_map is None:
            routing_map = self._build_routing_map()
            self.cache.set('routes', routing_map)
        return routing_map

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
#        if 'sitemap' in self.podspec:
#            sitemap_path = self.podspec['sitemap'].get('path')
#            sitemap_path = self.format_path(sitemap_path)
#            controller = sitemap.SitemapController(
#                pod=self.pod,
#                path=sitemap_path,
#                collections=self.podspec['sitemap'].get('collections'),
#                locales=self.podspec['sitemap'].get('locales'))
#            rules.append(routing.Rule(controller.path, endpoint=controller))
#        if 'static_dir' in self.pod.flags:
#            path = self.pod.flags['static_dir'] + '<grow:filename>'
#            endpoint = messages.Route
#            controller = static.StaticController(
#                path_format=path, source_format=path, pod=self.pod)
#            rules.append(routing.Rule(path, endpoint=controller))
        if 'static_dirs' in self.podspec:
            for config in self.podspec['static_dirs']:
                if config.get('dev') and not self.pod.env.dev:
                    continue
                static_dir = config['static_dir'] + '<grow:filename>'
                serve_at = config['serve_at'] + '<grow:filename>'
                serve_at = self.format_path(serve_at)
                localization = config.get('localization')
                fingerprinted = config.get('fingerprinted', False)
                route = messages.StaticRoute(
                    path_format=serve_at,
                    pod_path_format=static_dir,
                    localized=False,
                    fingerprinted=fingerprinted)
#                controller = static.StaticController(path_format=serve_at,
#                                                     source_format=static_dir,
#                                                     localized=False,
#                                                     localization=localization,
#                                                     fingerprinted=fingerprinted,
#                                                     pod=self.pod)
                rules.append(routing.Rule(route.path_format, endpoint=route))
#                if localization:
#                    localized_serve_at = localization.get('serve_at') + '<grow:filename>'
#                    static_dir = localization.get('static_dir')
#                    localized_static_dir = static_dir + '<grow:filename>'
#                    rule_path = localized_serve_at.replace('{locale}', '<grow:locale>')
#                    rule_path = self.format_path(rule_path)
#                    controller = static.StaticController(
#                        path_format=localized_serve_at,
#                        source_format=localized_static_dir,
#                        localized=True,
#                        localization=localization,
#                        fingerprinted=fingerprinted,
#                        pod=self.pod)
#                    rules.append(routing.Rule(rule_path, endpoint=controller))
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
            route, params = urls.match(path)
            if isinstance(route, messages.Route):
                pod_path = route.pod_path
                doc = self.pod.get_doc(pod_path, locale=params.get('locale'))
                controller = rendered.RenderedController(doc=doc, _pod=self.pod)
            elif isinstance(route, messages.StaticRoute):
                controller = static.StaticController(
                    path_format=route.path_format,
                    source_format=route.pod_path_format,
                    localized=route.localized,
                    pod=self.pod)
            return controller, params
        except routing.NotFound:
            raise webob.exc.HTTPNotFound('{} not found.'.format(path))

    def match_error(self, path, status=404):
        if status == 404 and self.pod.error_routes:
            view = self.pod.error_routes.get('default')
            return rendered.RenderedController(view=view, _pod=self.pod)

    def get_locales_to_paths(self):
        locales_to_paths = collections.defaultdict(list)
        for route in self:
            controller = route.endpoint
            paths = controller.list_concrete_paths()
            locale = controller.locale
            locales_to_paths[locale] += paths
        return locales_to_paths

    def get_controllers_to_paths(self):
        controllers_to_paths = collections.defaultdict(list)
        for route in self:
            controller = route.endpoint
            name = str(controller)
            paths = controller.list_concrete_paths()
            controllers_to_paths[name] += paths
            controllers_to_paths[name].sort()
        return controllers_to_paths

    @utils.memoize
    def list_concrete_paths(self):
        paths = set()
        for route in self:
            controller = route.endpoint
            new_paths = set(controller.list_concrete_paths())
            paths.update(new_paths)
        return list(paths)
