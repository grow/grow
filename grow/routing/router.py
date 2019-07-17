"""Router for grow documents."""

from grow.common import logger as grow_logger
from grow.performance import profile
from grow.routing import path_filter as grow_path_filter
from grow.routing import routes as grow_routes


class Error(Exception):
    """Base router error."""
    pass


class MissingStaticConfigError(Exception):
    """Error for missing a configuration for a static file."""
    pass


class Router(grow_logger.Logger, profile.Profiler):
    """Pod Router."""

    def __init__(self, *args, path_filter=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.path_filter = path_filter or grow_path_filter.PathFilter()
        self._routes = grow_routes.Routes()

    @property
    def routes(self):
        """Routes reflective of the docs."""
        return self._routes

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
        with self.profiler.timer('Router.add_docs'):
            skipped_paths = []
            for doc in docs:
                if not doc.has_serving_path():
                    continue
                if not self.path_filter.is_valid(doc.get_serving_path()):
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
                        for locale, path in localized_paths.items():
                            self.routes.add(path, RouteInfo('doc', {
                                'pod_path': doc.pod_path,
                                'locale': str(locale),
                            }), options=doc.path_params)
                    else:
                        self.routes.add(localized_path, RouteInfo('doc', {
                            'pod_path': doc.pod_path,
                        }), options=doc.path_params_localized)
            if skipped_paths:
                self.logger.info(
                    'Ignored {} documents.'.format(len(skipped_paths)))

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
                if 'locale' in route_info.meta and route_info.meta['locale']:
                    return route_info.meta['locale'] in locales
                # Build non-locale based routes with none locale.
                return None in locales
            self.routes.filter(_filter_locales)

    # def get_render_controller(self, pod, path, route_info, params=None):
    #     """Find the correct render controller for the given route info."""
    #     return render_controller.RenderController.from_route_info(
    #         pod, path, route_info, params=params)

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
