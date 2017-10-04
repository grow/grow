"""Router for grow documents."""

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
        self._routes = None

    @property
    def routes(self):
        """Routes reflective of the docs."""
        if not self._routes:
            self._routes = grow_routes.Routes()
        return self._routes

    def add_all_docs(self, concrete=True):
        """Add all pod docs to the router."""
        docs = []
        for collection in self.pod.list_collections():
            for doc in collection.list_servable_documents(
                    include_hidden=True, inject=False):
                docs.append(doc)
        self.add_docs(docs)

        podspec = self.pod.podspec.get_config()

        if 'sitemap' in podspec:
            sitemap = podspec['sitemap']
            sitemap_path = self.pod.path_format.format_pod(sitemap.get('path'))

            self.routes.add(sitemap_path, RouteInfo('sitemap', {
                'collections': sitemap.get('collections'),
                'locales': sitemap.get('locales'),
                'template': sitemap.get('template'),
                'path': sitemap_path,
            }))

        if 'static_dirs' in podspec:
            for config in podspec['static_dirs']:
                if config.get('dev') and not self.pod.env.dev:
                    continue
                if concrete:
                    # TODO: Enumerate static dirs
                    pass
                else:
                    serve_at = self.pod.path_format.format_pod(
                        config['serve_at'] + '*')
                    localization = config.get('localization')
                    fingerprinted = config.get('fingerprinted', False)
                    self.routes.add(serve_at, RouteInfo('static', {
                        'path_format': serve_at,
                        'source_format': config.get('static_dir') + '*',
                        'localized': False,
                        'localization': localization,
                        'fingerprinted': fingerprinted,
                    }))

                    if localization:
                        localized_serve_at = localization.get('serve_at') + '*'
                        self.routes.add(localized_serve_at, RouteInfo('static', {
                            'path_format': localized_serve_at,
                            'source_format': localization.get('static_dir') + '*',
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

    def add_docs(self, docs):
        """Add docs to the router."""
        # Force preload the docs since retrieving the doc locale and path require
        # the doc to be loaded. Attempts to thread this process.
        docs_loader.DocsLoader.load(docs)

        for doc in docs:
            if not doc.has_serving_path():
                continue
            self.routes.add(doc.get_serving_path(), RouteInfo('doc', {
                'pod_path': doc.pod_path,
                'locale': str(doc.locale),
            }))

    def get_render_controller(self, route_info):
        """Find the correct render controller for the given route info."""
        return render_controller.RenderController.from_route_info(
            self.pod, route_info)


# pylint: disable=too-few-public-methods
class RouteInfo(object):
    """Organize information stored in the routes."""

    def __init__(self, kind, meta=None):
        self.kind = kind
        self.meta = meta or {}
