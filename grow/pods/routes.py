"""Routes for document path routing."""

import collections
# NOTE: exc imported directly, webob.exc doesn't work when frozen.
from webob import exc as webob_exc
from werkzeug import routing
from grow.common import timer
from grow.common import utils
from grow.translations import locales
from . import messages
from . import rendered
from . import sitemap
from . import static


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

    @staticmethod
    def from_docs(pod, docs):
        """Create a routes object from a set of documents."""
        routes = Routes(pod)
        # pylint: disable=protected-access
        routes._build_routing_map_from_docs(docs)
        return routes

    def _add_document(self, doc):
        rule, _ = self._create_rule_for_doc(doc)
        if not rule:
            return
        self._routing_rules.append(rule)

    def _build_routing_map(self, inject=False):
        self._routing_rules = []

        # Content documents.
        def _get_all_docs():
            for collection in self.pod.list_collections():
                for doc in collection.list_servable_documents(include_hidden=True, inject=inject):
                    yield doc

        doc_routing_rules, new_paths_to_locales_to_docs = self._build_rules_from_docs(
            _get_all_docs())
        self._routing_rules += doc_routing_rules
        self._paths_to_locales_to_docs = new_paths_to_locales_to_docs

        # Static routes.
        self._routing_rules += self._build_static_routing_map_and_return_rules()

        self._recreate_routing_map()
        return self._routing_map

    def _build_routing_map_from_docs(self, docs):
        self._routing_rules = []

        doc_routing_rules, new_paths_to_locales_to_docs = self._build_rules_from_docs(
            docs)
        self._routing_rules += doc_routing_rules
        self._paths_to_locales_to_docs = new_paths_to_locales_to_docs

        self._recreate_routing_map()
        return self._routing_map

    def _build_rules_from_docs(self, docs):
        new_paths_to_locales_to_docs = collections.defaultdict(dict)
        routing_rules = []
        serving_paths_to_docs = {}
        duplicate_paths = collections.defaultdict(list)

        # Content documents.
        with self.pod.profile.timer('Routes._build_rules_from_docs'):
            for doc in self._clean_doc_locales(docs):
                rule, serving_path = self._create_rule_for_doc(doc)
                if not rule:
                    continue
                if serving_path in serving_paths_to_docs:
                    duplicate_paths[serving_path].append(
                        serving_paths_to_docs[serving_path])
                    duplicate_paths[serving_path].append(doc)
                serving_paths_to_docs[serving_path] = doc
                routing_rules.append(rule)
                new_paths_to_locales_to_docs[doc.pod_path][doc.locale] = doc

        if duplicate_paths:
            text = 'Found duplicate serving paths: {}'
            raise DuplicatePathsError(text.format(dict(duplicate_paths)))
        return routing_rules, new_paths_to_locales_to_docs

    def _build_static_routing_map_and_return_rules(self):
        with self.pod.profile.timer(
                'Routes._build_static_routing_map_and_return_rules'):
            rules = self.list_static_routes()
            self._static_routing_map = routing.Map(
                rules, converters=Routes.converters)
            return [rule.empty() for rule in rules]

    def _clean_doc_locales(self, docs):
        """Fixes docs loaded without a locale but that define a different default locale."""

        root_to_locale = {}

        # Track the paths that have been cleaned to not return default_doc if it
        # already has been yielded.
        cleaned_paths = []
        yield_paths = []

        for doc in docs:
            if not doc.has_serving_path():
                continue
            # Ignore the docs that are the same as the default locale.
            root_path = doc.root_pod_path
            current_locale = str(doc.locale)
            if root_path in root_to_locale and current_locale in root_to_locale[root_path]:
                continue
            if doc._locale_kwarg is None and str(doc.locale_safe) != current_locale:
                col_default_locale = str(doc.collection.default_locale)
                valid_locales = [str(l) for l in doc.locales]

                # The None locale is now invalid in the cache since the
                # front-matter differs.
                self.pod.podcache.collection_cache.remove_document_locale(
                    doc, doc.locale_safe)

                # Need to also yield the collection default if it differs and
                # is available.
                if col_default_locale != current_locale and col_default_locale in valid_locales:
                    default_doc = doc.localize(col_default_locale)
                    if (default_doc.exists
                            and col_default_locale == str(default_doc.locale)
                            and default_doc.get_serving_path() not in yield_paths):
                        yield_paths.append(default_doc.get_serving_path())
                        cleaned_paths.append(default_doc.get_serving_path())
                        yield default_doc

                clean_doc = doc.localize(current_locale)

                # Store the actual default locale (based off front-matter) to
                # the cache.
                self.pod.podcache.collection_cache.add_document_locale(
                    clean_doc, None)

                if root_path not in root_to_locale:
                    root_to_locale[root_path] = []
                if current_locale not in root_to_locale[root_path]:
                    root_to_locale[root_path].append(current_locale)
                yield_paths.append(clean_doc.get_serving_path())
                cleaned_paths.append(clean_doc.get_serving_path())
                yield clean_doc
            else:
                if doc.get_serving_path() in cleaned_paths:
                    continue
                yield_paths.append(doc.get_serving_path())
                yield doc

    def _create_rule_for_doc(self, doc):
        if not doc.has_serving_path():
            return None, None
        serving_path = doc.get_serving_path()
        controller = rendered.RenderedController(
            view=doc.view, doc=doc, _pod=self.pod)
        return routing.Rule(serving_path, endpoint=controller), serving_path

    def _recreate_routing_map(self):
        with self.pod.profile.timer('Routes._recreate_routing_map'):
            rules = [rule.empty() for rule in self._routing_rules]
            self._routing_map = routing.Map(
                rules, converters=Routes.converters)

    def _remove_document(self, doc):
        rule, serving_path = self._create_rule_for_doc(doc)
        if not rule:
            return

        # The `.remove()` does not work correctly for rules.
        old_rules = self._routing_rules
        self._routing_rules = []
        for rule in old_rules:
            if rule.rule != serving_path:
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
        if self.pod.env.fingerprint:
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
        if 'static_dirs' in self.podspec:
            for config in self.podspec['static_dirs']:
                if config.get('dev') and not self.pod.env.dev:
                    continue
                static_dir = config.get('static_dir')
                # Skip the multi-static directories for old routing.
                if not static_dir:
                    continue
                static_dir = static_dir + '<grow:filename>'
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
                    localized_serve_at = localization.get(
                        'serve_at') + '<grow:filename>'
                    static_dir = localization.get('static_dir')
                    localized_static_dir = static_dir + '<grow:filename>'
                    rule_path = localized_serve_at.replace(
                        '{locale}', '<grow:locale>')
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
            raise webob_exc.HTTPBadRequest('Invalid path.')
        urls = self.routing_map.bind_to_environ(env)
        try:
            controller, params = urls.match(path)
            return controller, params
        except routing.NotFound:
            raise webob_exc.HTTPNotFound('{} not found.'.format(path))

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
            with timer.Timer() as t:
                self._build_routing_map(inject=False)
            self.pod.logger.info('Routes rebuilt in {:.3f} s'.format(t.secs))

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
