"""Router for grow documents."""

import os
from grow.performance import docs_loader
from grow.rendering import render_controller
from grow.routing import routes as grow_routes


class Error(Exception):
    """Base router error."""
    pass


class Router(object):
    """Router for pods."""

    def __init__(self, pod):
        self.pod = pod
        self._routes = grow_routes.Routes()

    @property
    def routes(self):
        """Routes reflective of the docs."""
        return self._routes

    def add_all(self, concrete=True):
        """Add all documents and static content."""

        self.add_all_docs(concrete=concrete)
        self.add_all_static(concrete=concrete)
        # self.add_all_other()

    def add_all_docs(self, concrete=True):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_docs'):
            docs = []
            for collection in self.pod.list_collections():
                for doc in collection.list_docs_unread():
                    docs.append(doc)

            # Force preload the docs.
            docs_loader.DocsLoader.load(docs)
            docs_loader.DocsLoader.fix_default_locale(self.pod, docs)
            if concrete:
                # Will need all of the docs, so expand them out and preload.
                docs = docs_loader.DocsLoader.expand_locales(self.pod, docs)
                docs_loader.DocsLoader.load(docs)

            self.add_docs(docs, concrete=concrete)

    def add_all_other(self):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_other'):
            podspec = self.pod.podspec.get_config()
            if 'sitemap' in podspec:
                sitemap = podspec['sitemap']
                sitemap_path = self.pod.path_format.format_pod(
                    sitemap.get('path'))

                self.routes.add(sitemap_path, RouteInfo('sitemap', {
                    'collections': sitemap.get('collections'),
                    'locales': sitemap.get('locales'),
                    'template': sitemap.get('template'),
                    'path': sitemap_path,
                }))

    def add_all_static(self, concrete=True):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_static'):
            podspec = self.pod.podspec.get_config()
            if 'static_dirs' in podspec:
                for config in podspec['static_dirs']:
                    if config.get('dev') and not self.pod.env.dev:
                        continue

                    fingerprinted = config.get('fingerprinted', False)
                    localization = config.get('localization')

                    if concrete or fingerprinted:
                        # Enumerate static files.
                        for root, dirs, files in self.pod.walk(config.get('static_dir')):
                            for directory in dirs:
                                if directory.startswith('.'):
                                    dirs.remove(directory)
                            pod_dir = root.replace(self.pod.root, '')
                            for file_name in files:
                                pod_path = os.path.join(pod_dir, file_name)
                                # TODO figure out locale...
                                static_doc = self.pod.get_static(
                                    pod_path, locale=None)
                                self.routes.add(
                                    static_doc.serving_path, RouteInfo('static', {
                                        'pod_path': static_doc.pod_path,
                                        'locale': None,
                                        'localized': False,
                                        'localization': localization,
                                        'fingerprinted': fingerprinted,
                                    }))
                    else:
                        serve_at = self.pod.path_format.format_pod(
                            config['serve_at'])
                        self.routes.add(serve_at + '*', RouteInfo('static', {
                            'path_format': serve_at,
                            'source_format': config.get('static_dir'),
                            'localized': False,
                            'localization': localization,
                            'fingerprinted': fingerprinted,
                        }))

                        if localization:
                            localized_serve_at = self.pod.path_format.format_pod(
                                localization.get('serve_at'))
                            self.routes.add(localized_serve_at + '*', RouteInfo('static', {
                                'path_format': localized_serve_at,
                                'source_format': localization.get('static_dir'),
                                'localized': True,
                                'localization': localization,
                                'fingerprinted': fingerprinted,
                            }))

    def add_doc(self, doc):
        """Add doc to the router."""
        if not doc.has_serving_path():
            return
        self.routes.add(doc.get_serving_path(), RouteInfo('doc', {
            'pod_path': doc.pod_path,
            'locale': str(doc.locale),
        }))

    def add_docs(self, docs, concrete=True):
        """Add docs to the router."""
        with self.pod.profile.timer('Router.add_docs'):
            for doc in docs:
                if doc.hidden or not doc.has_serving_path():
                    continue
                if concrete:
                    # Concrete iterates all possible documents.
                    self.routes.add(doc.get_serving_path(), RouteInfo('doc', {
                        'pod_path': doc.pod_path,
                        'locale': str(doc.locale),
                    }))
                else:
                    # Use the raw paths to parameterize the routing.
                    base_path = doc.get_serving_path_base()
                    if base_path:
                        self.routes.add(base_path, RouteInfo('doc', {
                            'pod_path': doc.pod_path,
                            'locale': str(doc.locale),
                        }))
                    localized_path = doc.get_serving_path_localized()
                    if not localized_path or ':locale' not in localized_path:
                        localized_paths = doc.get_serving_paths_localized()
                        for locale, path in localized_paths.iteritems():
                            self.routes.add(path, RouteInfo('doc', {
                                'pod_path': doc.pod_path,
                                'locale': str(locale),
                            }))
                    else:
                        self.routes.add(localized_path, RouteInfo('doc', {
                            'pod_path': doc.pod_path,
                        }))

    def add_pod_paths(self, pod_paths, concrete=True):
        """Add pod paths to the router."""
        with self.pod.profile.timer('Router.add_pod_paths'):
            docs = []
            for pod_path in pod_paths:
                depedents = self.pod.podcache.dependency_graph.match_dependents(
                    pod_path)
                for dep_path in depedents:
                    docs.append(self.pod.get_doc(dep_path))

            # Force preload the docs.
            docs_loader.DocsLoader.load(docs)
            docs_loader.DocsLoader.fix_default_locale(self.pod, docs)
            if concrete:
                # Will need all of the docs, so expand them out and preload.
                docs = docs_loader.DocsLoader.expand_locales(self.pod, docs)
                docs_loader.DocsLoader.load(docs)
            self.add_docs(docs, concrete=concrete)

    def get_render_controller(self, path, route_info, params=None):
        """Find the correct render controller for the given route info."""
        return render_controller.RenderController.from_route_info(
            self.pod, path, route_info, params=params)

    def use_simple(self):
        """Switches the routes to be a simple routes object."""
        previous_routes = self._routes
        self._routes = grow_routes.RoutesSimple()
        if previous_routes is not None:
            for path, value in previous_routes.nodes:
                self._routes.add(path, value)

# pylint: disable=too-few-public-methods


class RouteInfo(object):
    """Organize information stored in the routes."""

    def __init__(self, kind, meta=None):
        self.kind = kind
        self.meta = meta or {}
