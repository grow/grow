from . import locales
from . import messages
from . import rendered
from . import sitemap
from . import static
from grow.common import utils
from werkzeug import routing
import collections
import webob
import werkzeug


class Error(Exception):
    pass


class DuplicatePathsError(Error, ValueError):
    pass


class GrowConverter(routing.PathConverter):
    pass


class Routes(object):
    converters = {'grow': GrowConverter}

    def __init__(self, pod):
        self.pod = pod
        self._paths_to_locales_to_docs = collections.defaultdict(dict)
        self._routing_map = None
        self._static_routing_map = None
        self._routing_rules = []

    def __iter__(self):
        return self.routing_map.iter_rules()

    def _add_document(self, doc):
        rule, serving_path = self._create_rule_for_doc(doc)
        if not rule:
            return
        self._routing_rules.append(rule)

    def _build_routing_map(self, inject=False):
        new_paths_to_locales_to_docs = collections.defaultdict(dict)
        self._routing_rules = []
        serving_paths_to_docs = {}
        duplicate_paths = collections.defaultdict(list)

        # Content documents.
        for collection in self.pod.list_collections():
            for doc in collection.list_servable_documents(include_hidden=True, inject=inject):
                rule, serving_path = self._create_rule_for_doc(doc)
                if serving_path in serving_paths_to_docs:
                    duplicate_paths[serving_path].append(serving_paths_to_docs[serving_path])
                    duplicate_paths[serving_path].append(doc)
                serving_paths_to_docs[serving_path] = doc
                self._routing_rules.append(rule)
                new_paths_to_locales_to_docs[doc.pod_path][doc.locale] = doc

        # Static routes.
        self._routing_rules += self._build_static_routing_map_and_return_rules()

        self._recreate_routing_map()
        self._paths_to_locales_to_docs = new_paths_to_locales_to_docs
        if duplicate_paths:
            text = 'Found duplicate serving paths: {}'
            raise DuplicatePathsError(text.format(dict(duplicate_paths)))
        return self._routing_map

    def _build_static_routing_map_and_return_rules(self):
        rules = self.list_static_routes()
        self._static_routing_map = routing.Map(rules, converters=Routes.converters)
        return [rule.empty() for rule in rules]

    def _create_rule_for_doc(self, doc):
        if not doc.has_serving_path():
            return None, None
        serving_path = doc.get_serving_path()
        controller = rendered.RenderedController(
            view=doc.view, doc=doc, _pod=self.pod)
        return routing.Rule(serving_path, endpoint=controller), serving_path

    def _recreate_routing_map(self):
        rules = [rule.empty() for rule in self._routing_rules]
        self._routing_map = routing.Map(rules, converters=Routes.converters)

    def _remove_document(self, doc):
        rule, serving_path = self._create_rule_for_doc(doc)
        if not rule:
            return

        # The `.remove()` does not work correctly for rules.
        old_rules = self._routing_rules
        self._routing_rules = []
        for rule in old_rules:
            if rule.rule is not serving_path:
                self._routing_rules.append(rule)

    @property
    def podspec(self):
        return self.pod.get_podspec().get_config()

    def add_document(self, doc):
        self._add_document(doc)
        self._recreate_routing_map()

    def add_documents(self, docs):
        for doc in docs:
            self._add_document(doc)
        self._recreate_routing_map()

    def format_path(self, path):
        path = '' if path is None else path
        if 'root' in self.podspec:
            path = path.replace('{root}', self.podspec['root'])
        path = path.replace('{env.fingerprint}', self.pod.env.fingerprint)
        path = path.replace('{fingerprint}', '<grow:fingerprint>')
        path = path.replace('//', '/')
        return path

    def get_controllers_to_paths(self):
        controllers_to_paths = collections.defaultdict(list)
        for route in self:
            controller = route.endpoint
            name = str(controller)
            paths = controller.list_concrete_paths()
            controllers_to_paths[name] += paths
            controllers_to_paths[name].sort()
        return controllers_to_paths

    def get_doc(self, path, locale=None):
        if isinstance(locale, basestring):
            locale = locales.Locale(locale)
        return self._paths_to_locales_to_docs.get(path, {}).get(locale)

    def get_locales_to_paths(self):
        locales_to_paths = collections.defaultdict(list)
        for route in self:
            controller = route.endpoint
            paths = controller.list_concrete_paths()
            locale = controller.locale
            locales_to_paths[locale] += paths
        return locales_to_paths

    @utils.memoize
    def list_concrete_paths(self):
        paths = set()
        for route in self:
            controller = route.endpoint
            new_paths = set(controller.list_concrete_paths())
            paths.update(new_paths)
        return list(paths)

    def list_static_routes(self):
        rules = []
        # Auto-generated from flags.
        if 'sitemap' in self.podspec:
            sitemap_path = self.podspec['sitemap'].get('path')
            sitemap_path = self.format_path(sitemap_path)
            controller = sitemap.SitemapController(
                pod=self.pod,
                path=sitemap_path,
                collections=self.podspec['sitemap'].get('collections'),
                locales=self.podspec['sitemap'].get('locales'),
                template=self.podspec['sitemap'].get('template'))
            rules.append(routing.Rule(controller.path, endpoint=controller))
        if 'static_dir' in self.pod.flags:
            path = self.pod.flags['static_dir'] + '<grow:filename>'
            controller = static.StaticController(
                path_format=path, source_format=path, pod=self.pod)
            rules.append(routing.Rule(path, endpoint=controller))
        if 'static_dirs' in self.podspec:
            for config in self.podspec['static_dirs']:
                if config.get('dev') and not self.pod.env.dev:
                    continue
                static_dir = config['static_dir'] + '<grow:filename>'
                serve_at = config['serve_at'] + '<grow:filename>'
                serve_at = self.format_path(serve_at)
                localization = config.get('localization')
                fingerprinted = config.get('fingerprinted', False)
                controller = static.StaticController(path_format=serve_at,
                                                     source_format=static_dir,
                                                     localized=False,
                                                     localization=localization,
                                                     fingerprinted=fingerprinted,
                                                     pod=self.pod)
                rules.append(routing.Rule(serve_at, endpoint=controller))
                if localization:
                    localized_serve_at = localization.get('serve_at') + '<grow:filename>'
                    static_dir = localization.get('static_dir')
                    localized_static_dir = static_dir + '<grow:filename>'
                    rule_path = localized_serve_at.replace('{locale}', '<grow:locale>')
                    rule_path = self.format_path(rule_path)
                    controller = static.StaticController(
                        path_format=localized_serve_at,
                        source_format=localized_static_dir,
                        localized=True,
                        localization=localization,
                        fingerprinted=fingerprinted,
                        pod=self.pod)
                    rules.append(routing.Rule(rule_path, endpoint=controller))
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
            controller, params = urls.match(path)
            return controller, params
        except routing.NotFound:
            raise webob.exc.HTTPNotFound('{} not found.'.format(path))

    def match_error(self, path, status=404):
        if status == 404 and self.pod.error_routes:
            view = self.pod.error_routes.get('default')
            return rendered.RenderedController(view=view, _pod=self.pod)

    def reconcile_documents(self, remove_docs=None, add_docs=None):
        for doc in remove_docs if remove_docs else []:
            self._remove_document(doc)
        for doc in add_docs if add_docs else []:
            self._add_document(doc)
        self._recreate_routing_map()

    def remove_document(self, doc):
        self._remove_document(doc)
        self._recreate_routing_map()

    def remove_documents(self, docs):
        for doc in docs:
            self._remove_document(doc)
        self._recreate_routing_map()

    def reset_cache(self, rebuild=True, inject=False):
        if rebuild:
            self.pod.podcache.reset()
            self._build_routing_map(inject=False)

    @property
    def routing_map(self):
        if self._routing_map is None:
            self._build_routing_map()
        return self._routing_map

    @property
    def static_routing_map(self):
        if self._static_routing_map is None:
            self._build_static_routing_map_and_return_rules()
        return self._static_routing_map

    def to_message(self):
        message = messages.RoutesMessage()
        message.routes = []
        for route in self:
            controller = route.endpoint
            message.routes.extend(controller.to_route_messages())
        return message
