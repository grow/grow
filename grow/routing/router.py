"""Router for grow documents."""

import os
from grow.performance import docs_loader
from grow.rendering import render_controller
from grow.routing import path_filter as grow_path_filter
from grow.routing import routes as grow_routes


class Error(Exception):
    """Base router error."""
    pass


class MissingStaticConfigError(Exception):
    """Error for missing a configuration for a static file."""
    pass


class Router(object):
    """Router for pods."""

    def __init__(self, pod):
        self.pod = pod
        self._routes = grow_routes.Routes()

    def _preload_and_expand(self, docs, expand=True):
        # Force preload the docs.
        docs_loader.DocsLoader.load(docs)
        docs_loader.DocsLoader.fix_default_locale(self.pod, docs)
        if expand:
            # Will need all of the docs, so expand them out and preload.
            docs = docs_loader.DocsLoader.expand_locales(self.pod, docs)
            docs_loader.DocsLoader.load(docs)
        return docs

    @property
    def routes(self):
        """Routes reflective of the docs."""
        return self._routes

    def add_all(self, concrete=True):
        """Add all documents and static content."""

        self.add_all_docs(concrete=concrete)
        self.add_all_static(concrete=concrete)
        self.add_all_other()

    def add_all_docs(self, concrete=True):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_docs'):
            docs = []
            doc_basenames = set()
            for collection in self.pod.list_collections():
                for doc in collection.list_docs_unread():
                    # Skip duplicate documents when using non-concrete routing.
                    if not concrete and doc.basename in doc_basenames:
                        continue
                    is_default_locale = doc._locale_kwarg == self.pod.podspec.default_locale
                    # Ignore localized names in the files since they will be
                    # picked up when the locales are expanded.
                    if doc.root_pod_path == doc.pod_path or is_default_locale:
                        docs.append(doc)
                        doc_basenames.add(doc.basename)
                    else:
                        # If this document does not exist with the default
                        # locale it still needs to be added.
                        locale_doc = self.pod.get_doc(doc.pod_path, doc.default_locale)
                        if not locale_doc.exists:
                            docs.append(doc)
                            doc_basenames.add(doc.basename)
            docs = self._preload_and_expand(docs, expand=concrete)
            self.add_docs(docs, concrete=concrete)

    def add_all_other(self):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_other'):
            podspec = self.pod.podspec.get_config()
            if 'error_routes' in podspec:
                for key, error_route in podspec['error_routes'].iteritems():
                    if key == 'default':
                        key = 404

                    self.routes.add('/{}.html'.format(key), RouteInfo('error', {
                        'key': key,
                        'view': error_route,
                    }))

            if 'sitemap' in podspec:
                sitemap = podspec['sitemap']
                sitemap_path = self.pod.path_format.format_pod(
                    sitemap.get('path', '/sitemap.xml'))
                self.routes.add(sitemap_path, RouteInfo('sitemap', {
                    'collections': sitemap.get('collections'),
                    'locales': sitemap.get('locales'),
                    'template': sitemap.get('template'),
                    'path': sitemap_path,
                }))

    def add_all_static(self, concrete=True):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_static'):
            skipped_paths = []
            for config in self.pod.static_configs:
                if config.get('dev') and not self.pod.env.dev:
                    continue

                fingerprinted = config.get('fingerprinted', False)
                localization = config.get('localization')
                static_filter = config.get('filter', {})
                if static_filter:
                    path_filter = grow_path_filter.PathFilter(
                        static_filter.get('ignore_paths'), static_filter.get('include_paths'))
                else:
                    path_filter = self.pod.path_filter

                static_dirs = config.get('static_dirs')
                if not static_dirs:
                    static_dirs = [config.get('static_dir')]

                if localization:
                    localized_static_dirs = localization.get('static_dirs')
                    if not localized_static_dirs:
                        localized_static_dirs = [localization.get('static_dir')]

                if concrete or fingerprinted:
                    # Enumerate static files.
                    for static_dir in static_dirs:
                        for root, dirs, files in self.pod.walk(static_dir):
                            for directory in dirs:
                                if directory.startswith('.'):
                                    dirs.remove(directory)
                            pod_dir = root.replace(self.pod.root, '')
                            for file_name in files:
                                pod_path = os.path.join(pod_dir, file_name)
                                static_doc = self.pod.get_static(pod_path, locale=None)
                                self.add_static_doc(static_doc)
                    if localization:
                        # TODO handle the localized static files?
                        pass
                else:
                    serve_at = self.pod.path_format.format_pod(
                        config['serve_at'], parameterize=True)
                    self.routes.add(serve_at + '*', RouteInfo('static', {
                        'path_format': serve_at,
                        'source_formats': static_dirs,
                        'localized': False,
                        'localization': localization,
                        'fingerprinted': fingerprinted,
                        'static_filter': static_filter,
                        'path_filter': path_filter,
                    }))

                    if localization:
                        localized_serve_at = self.pod.path_format.format_pod(
                            localization.get('serve_at'), parameterize=True)
                        self.routes.add(localized_serve_at + '*', RouteInfo('static', {
                            'path_format': localized_serve_at,
                            'source_formats': localized_static_dirs,
                            'localized': True,
                            'localization': localization,
                            'fingerprinted': fingerprinted,
                            'static_filter': static_filter,
                            'path_filter': path_filter,
                        }))
            if skipped_paths:
                self.pod.logger.info(
                    'Ignored {} static files.'.format(len(skipped_paths)))

    def add_doc(self, doc):
        """Add doc to the router."""
        if not doc.has_serving_path():
            return
        self.routes.add(doc.get_serving_path(), RouteInfo('doc', {
            'pod_path': doc.pod_path,
            'locale': str(doc.locale),
        }), options=doc.path_params)

    def add_docs(self, docs, concrete=True):
        """Add docs to the router."""
        with self.pod.profile.timer('Router.add_docs'):
            skipped_paths = []
            for doc in docs:
                if not doc.has_serving_path():
                    continue
                if not self.pod.path_filter.is_valid(doc.get_serving_path()):
                    skipped_paths.append(doc.get_serving_path())
                    continue
                if concrete:
                    # Concrete iterates all possible documents.
                    self.routes.add(doc.get_serving_path(), RouteInfo('doc', {
                        'pod_path': doc.pod_path,
                        'locale': str(doc.locale),
                    }), options=doc.path_params)
                else:
                    # Use the raw paths to parameterize the routing.
                    base_path = doc.get_serving_path_base()
                    if base_path:
                        self.routes.add(base_path, RouteInfo('doc', {
                            'pod_path': doc.pod_path,
                            'locale': str(doc.locale),
                        }), options=doc.path_params)
                    localized_path = doc.get_serving_path_localized()
                    if not localized_path or ':locale' not in localized_path:
                        localized_paths = doc.get_serving_paths_localized()
                        for locale, path in localized_paths.iteritems():
                            self.routes.add(path, RouteInfo('doc', {
                                'pod_path': doc.pod_path,
                                'locale': str(locale),
                            }), options=doc.path_params)
                    else:
                        self.routes.add(localized_path, RouteInfo('doc', {
                            'pod_path': doc.pod_path,
                        }), options=doc.path_params_localized)
            if skipped_paths:
                self.pod.logger.info(
                    'Ignored {} documents.'.format(len(skipped_paths)))

    def add_pod_paths(self, pod_paths, concrete=True):
        """Add pod paths to the router."""
        with self.pod.profile.timer('Router.add_pod_paths'):
            docs = []
            for pod_path in pod_paths:
                depedents = self.pod.podcache.dependency_graph.match_dependents(
                    pod_path)
                for dep_path in depedents:
                    docs.append(self.pod.get_doc(dep_path))
            docs = self._preload_and_expand(docs, expand=concrete)
            self.add_docs(docs, concrete=concrete)

    def add_static_doc(self, static_doc):
        """Add static doc to the router."""
        if not static_doc.path_filter.is_valid(static_doc.serving_path):
            return
        self.routes.add(
            static_doc.serving_path, RouteInfo('static', {
                'pod_path': static_doc.pod_path,
                'locale': None,
                'localized': False,
                'localization': static_doc.config.get('localization'),
                'fingerprinted': static_doc.fingerprinted,
                'static_filter': static_doc.filter,
                'path_filter': static_doc.path_filter,
            }))

    def filter(self, locales=None):
        """Filter the routes based on a criteria."""
        if locales:
            # Ability to specify a none locale using commanf flag.
            if 'None' in locales:
                locales.append(None)

            def _filter_locales(route_info):
                if 'locale' in route_info.meta:
                    return route_info.meta['locale'] in locales
                # Build non-locale based routes with none locale.
                return None in locales
            self.routes.filter(_filter_locales)

    def get_render_controller(self, path, route_info, params=None):
        """Find the correct render controller for the given route info."""
        return render_controller.RenderController.from_route_info(
            self.pod, path, route_info, params=params)

    def get_static_config_for_pod_path(self, pod_path):
        """Return the static configuration for a pod path."""
        for config in self.pod.static_configs:
            if config.get('dev') and not self.pod.env.dev:
                continue
            static_dirs = config.get('static_dirs')
            if not static_dirs:
                static_dirs = [config.get('static_dir')]
            if isinstance(static_dirs, basestring):
                static_dirs = [static_dirs]
            for static_dir in static_dirs:
                if pod_path.startswith(static_dir):
                    return config
            intl = config.get('localization', {})
            if intl:
                static_dirs = intl.get('static_dirs')
                if not static_dirs:
                    static_dirs = [intl.get('static_dir')]
                if isinstance(static_dirs, basestring):
                    static_dirs = [static_dirs]
                for static_dir in static_dirs:
                    if pod_path.startswith(static_dir):
                        return config

        text = '{} is not found in any static file configuration in the podspec.'
        raise MissingStaticConfigError(text.format(pod_path))

    def reconcile_documents(self, remove_docs=None, add_docs=None):
        """Remove old docs and add new docs to the routes."""
        for doc in remove_docs if remove_docs else []:
            self.routes.remove(doc.get_serving_path())
        for doc in add_docs if add_docs else []:
            self.add_doc(doc)

    def use_simple(self):
        """Switches the routes to be a simple routes object."""
        previous_routes = self._routes
        self._routes = grow_routes.RoutesSimple()
        if previous_routes is not None:
            for path, value, _ in previous_routes.nodes:
                self._routes.add(path, value)


# pylint: disable=too-few-public-methods
class RouteInfo(object):
    """Organize information stored in the routes."""

    def __eq__(self, other):
        return self.kind == other.kind and self.meta == other.meta

    def __init__(self, kind, meta=None):
        self.kind = kind
        self.meta = meta or {}

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<RouteInfo kind={} meta={}>'.format(self.kind, self.meta)
