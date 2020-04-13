"""Router for grow documents."""

import fnmatch
import os
import re
from protorpc import messages
from grow.performance import docs_loader
from grow.rendering import render_controller
from grow.routing import path_filter as grow_path_filter
from grow.routing import routes as grow_routes


class FilterConfig(messages.Message):
    """Configuration for routing filters in podspec."""
    type = messages.StringField(1)
    collections = messages.StringField(2, repeated=True)
    paths = messages.StringField(3, repeated=True)
    locales = messages.StringField(4, repeated=True)
    kinds = messages.StringField(5, repeated=True)


class Error(Exception):
    """Base router error."""

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


class MissingStaticConfigError(Error):
    """Error for missing a configuration for a static file."""
    pass


class Router(object):
    """Router for pods."""

    def __init__(self, pod, routes=None):
        self.pod = pod
        self._routes = routes or grow_routes.Routes()

    def _preload_and_expand(self, docs, expand=True):
        # Force preload the docs.
        docs_loader.DocsLoader.load(self.pod, docs)
        docs_loader.DocsLoader.fix_default_locale(self.pod, docs)
        if expand:
            # Will need all of the docs, so expand them out and preload.
            docs = docs_loader.DocsLoader.expand_locales(self.pod, docs)
            docs_loader.DocsLoader.load(self.pod, docs)
        return docs

    @property
    def routes(self):
        """Routes reflective of the docs."""
        return self._routes

    def _add_to_routes(self, path, route_info, concrete=True, options=None, fingerprinted=None):
        """Add to the routes and the route cache."""
        self.routes.add(path, route_info, options=options)

        # Don't want to keep track of the concrete fingerprinted routes.
        if not concrete or not fingerprinted:
            self.pod.podcache.routes_cache.add(
                path, route_info, options=options, concrete=concrete,
                env=self.pod.env.name)

    def add_all(self, concrete=True, use_cache=True):
        """Add all documents and static content."""
        if use_cache:
            unchanged_pod_paths = self.from_cache(concrete=concrete)
        else:
            unchanged_pod_paths = []

        self.add_all_docs(
            concrete=concrete, unchanged_pod_paths=unchanged_pod_paths)
        self.add_all_static(
            concrete=concrete, unchanged_pod_paths=unchanged_pod_paths)
        self.add_all_other(concrete=concrete)
        self.add_all_hook(concrete=concrete)

    def add_all_docs(self, concrete=True, unchanged_pod_paths=None):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_docs'):
            unchanged_pod_paths = unchanged_pod_paths or set()
            docs = []
            for collection in self.pod.list_collections():
                doc_basenames = set()
                for doc in collection.list_docs_unread():
                    # Skip when the doc is in the unchanged pod paths set.
                    if doc.pod_path in unchanged_pod_paths:
                        # Even though it is being skipped, mark that it has been
                        # loaded to prevent issues with paramaterized serving paths.
                        doc_basenames.add(doc.collection_sub_path_clean)
                        continue
                    # Skip duplicate documents when using non-concrete routing.
                    if not concrete and doc.collection_sub_path_clean in doc_basenames:
                        continue
                    is_default_locale = doc._locale_kwarg == self.pod.podspec.default_locale
                    # Ignore localized names in the files since they will be
                    # picked up when the locales are expanded.
                    if doc.root_pod_path == doc.pod_path or is_default_locale:
                        docs.append(doc)
                        doc_basenames.add(doc.collection_sub_path_clean)
                    else:
                        # If this document does not exist with the default
                        # locale it still needs to be added.
                        locale_doc = self.pod.get_doc(
                            doc.pod_path, doc.default_locale)
                        if not locale_doc.exists:
                            docs.append(doc)
                            doc_basenames.add(doc.collection_sub_path_clean)
            docs = self._preload_and_expand(docs, expand=concrete)
            self.add_docs(docs, concrete=concrete)

    def add_all_hook(self, concrete=True):
        """Trigger the hook for adding all to the routes."""
        with self.pod.profile.timer('Router.add_all_hook'):
            self.pod.extensions_controller.trigger(
                'router_add', self, concrete=concrete)

    def add_all_other(self, concrete=True):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_other'):
            podspec = self.pod.podspec.get_config()
            if 'error_routes' in podspec:
                for key, error_route in podspec['error_routes'].items():
                    if key == 'default':
                        key = 404

                    path = '/{}.html'.format(key)
                    route_info = RouteInfo('error', meta={
                        'key': key,
                        'view': error_route,
                    })
                    self._add_to_routes(path, route_info, concrete=concrete)

            if 'sitemap' in podspec:
                sitemap = podspec['sitemap']
                default_sitemap_path = self.pod.podspec.root + '/sitemap.xml'
                default_sitemap_path = default_sitemap_path.replace('//', '/')
                sitemap_path = self.pod.path_format.format_pod(
                    sitemap.get('path', default_sitemap_path))
                route_info = RouteInfo('sitemap', meta={
                    'collections': sitemap.get('collections'),
                    'locales': sitemap.get('locales'),
                    'template': sitemap.get('template'),
                    'filters': sitemap.get('filters'),
                    'path': sitemap_path,
                })
                self._add_to_routes(
                    sitemap_path, route_info, concrete=concrete)

    def add_all_static(self, concrete=True, unchanged_pod_paths=None):
        """Add all pod docs to the router."""
        with self.pod.profile.timer('Router.add_all_static'):
            unchanged_pod_paths = unchanged_pod_paths or set()
            skipped_paths = []
            for config in self.pod.static_configs:
                if config.get('dev') and not self.pod.env.dev:
                    continue

                fingerprinted = config.get('fingerprinted', False)
                localization = config.get('localization')
                static_filter = config.get('filter', {})
                if static_filter:
                    path_filter = grow_path_filter.PathFilter(
                        static_filter.get('ignore_paths'),
                        static_filter.get('include_paths'))
                else:
                    path_filter = self.pod.path_filter

                static_dirs = config.get('static_dirs')
                if not static_dirs:
                    static_dirs = [config.get('static_dir')]

                if localization:
                    localized_static_dirs = localization.get('static_dirs')
                    if not localized_static_dirs:
                        localized_static_dirs = [
                            localization.get('static_dir')]

                if concrete:
                    # Enumerate static files.
                    for static_dir in static_dirs:
                        for root, dirs, files in self.pod.walk(static_dir):
                            for directory in dirs:
                                if directory.startswith('.'):
                                    dirs.remove(directory)
                            pod_dir = root.replace(self.pod.root, '')
                            for file_name in files:
                                pod_path = os.path.join(pod_dir, file_name)
                                # Skip when the doc is in the unchanged pod paths set.
                                if pod_path in unchanged_pod_paths:
                                    continue
                                static_doc = self.pod.get_static(
                                    pod_path, locale=None)
                                self.add_static_doc(
                                    static_doc, concrete=concrete)
                    if localization:
                        # TODO handle the localized static files?
                        pass
                else:
                    serve_at = self.pod.path_format.format_pod(
                        config['serve_at'], parameterize=True)
                    route_info = RouteInfo('static', meta={
                        'path_format': serve_at,
                        'source_formats': static_dirs,
                        'localized': False,
                        'localization': localization,
                        'fingerprinted': fingerprinted,
                        'static_filter': static_filter,
                        'path_filter': path_filter,
                    })
                    self._add_to_routes(
                        serve_at + '*', route_info, concrete=concrete,
                        fingerprinted=fingerprinted)

                    if localization:
                        localized_serve_at = self.pod.path_format.format_pod(
                            localization.get('serve_at'), parameterize=True)
                        route_info = RouteInfo('static', meta={
                            'path_format': localized_serve_at,
                            'source_formats': localized_static_dirs,
                            'localized': True,
                            'localization': localization,
                            'fingerprinted': fingerprinted,
                            'static_filter': static_filter,
                            'path_filter': path_filter,
                        })
                        self._add_to_routes(
                            localized_serve_at + '*', route_info, concrete=concrete,
                            fingerprinted=fingerprinted)
            if skipped_paths:
                self.pod.logger.info(
                    'Ignored {} static files.'.format(len(skipped_paths)))

    def add_doc(self, doc, concrete=True):
        """Add doc to the router."""
        if not doc.has_serving_path():
            return
        route_info = RouteInfo(
            'doc', pod_path=doc.pod_path,
            hashed=self.pod.hash_file(doc.pod_path),
            meta={
                'pod_path': doc.pod_path,
                'locale': str(doc.locale),
                'collection_path': doc.collection.pod_path,
            })
        self._add_to_routes(
            doc.get_serving_path(), route_info,
            concrete=concrete, options=doc.path_params)

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
                    route_info = RouteInfo(
                        'doc', pod_path=doc.pod_path,
                        hashed=self.pod.hash_file(doc.pod_path),
                        meta={
                            'pod_path': doc.pod_path,
                            'locale': str(doc.locale),
                            'collection_path': doc.collection.pod_path,
                        })
                    self._add_to_routes(
                        doc.get_serving_path(), route_info,
                        options=doc.path_params, concrete=concrete)
                else:
                    # Use the raw paths to parameterize the routing.
                    base_path = doc.get_serving_path_base()
                    only_localized = doc.path_format == doc.path_format_localized
                    # If the path is already localized only add the
                    # parameterized version of the path.
                    if base_path and not only_localized:
                        route_info = RouteInfo(
                            'doc', pod_path=doc.pod_path,
                            hashed=self.pod.hash_file(doc.pod_path),
                            meta={
                                'pod_path': doc.pod_path,
                                'locale': str(doc.locale),
                                'collection_path': doc.collection.pod_path,
                            })
                        self._add_to_routes(
                            base_path, route_info,
                            concrete=concrete, options=doc.path_params)
                    localized_path = doc.get_serving_path_localized()
                    if not localized_path or ':locale' not in localized_path:
                        localized_paths = doc.get_serving_paths_localized()
                        for locale, path in localized_paths.items():
                            route_info = RouteInfo(
                                'doc', pod_path=doc.pod_path,
                                hashed=self.pod.hash_file(doc.pod_path),
                                meta={
                                    'pod_path': doc.pod_path,
                                    'locale': str(locale),
                                    'collection_path': doc.collection.pod_path,
                                })
                            self._add_to_routes(
                                path, route_info,
                                concrete=concrete, options=doc.path_params)
                    else:
                        route_info = RouteInfo(
                            'doc', pod_path=doc.pod_path,
                            hashed=self.pod.hash_file(doc.pod_path),
                            meta={
                                'pod_path': doc.pod_path,
                                'collection_path': doc.collection.pod_path,
                            })
                        self._add_to_routes(
                            localized_path, route_info,
                            concrete=concrete, options=doc.path_params_localized)
            if skipped_paths:
                self.pod.logger.info(
                    'Ignored {} documents.'.format(len(skipped_paths)))

    def add_pod_paths(self, pod_paths, concrete=True):
        """Add pod paths to the router."""
        with self.pod.profile.timer('Router.add_pod_paths'):
            # Find all of the doc pod_path for matching.
            all_doc_pod_paths = set()
            for collection in self.pod.list_collections():
                for doc in collection.list_docs_unread():
                    all_doc_pod_paths.add(doc.pod_path)

            doc_pod_paths = set()
            for pod_path in pod_paths:
                # Add docs from the depdency graph.
                dependents = self.pod.podcache.dependency_graph.match_dependents(
                    pod_path)
                for dep_path in dependents:
                    doc_pod_paths.add(dep_path)

                # Add docs based just on the doc pod paths.
                for doc_pod_path in all_doc_pod_paths:
                    if fnmatch.fnmatch(doc_pod_path, pod_path):
                        doc_pod_paths.add(doc_pod_path)

            docs = []
            for pod_path in doc_pod_paths:
                docs.append(self.pod.get_doc(pod_path))
            docs = self._preload_and_expand(docs, expand=concrete)
            self.add_docs(docs, concrete=concrete)

    def add_static_doc(self, static_doc, concrete=True):
        """Add static doc to the router."""
        if not static_doc.path_filter.is_valid(static_doc.serving_path):
            return
        route_info = RouteInfo(
            'static', pod_path=static_doc.pod_path,
            hashed=self.pod.hash_file(static_doc.pod_path),
            meta={
                'pod_path': static_doc.pod_path,
                'locale': None,
                'localized': False,
                'localization': static_doc.config.get('localization'),
                'fingerprinted': static_doc.fingerprinted,
                'static_filter': static_doc.filter,
                'path_filter': static_doc.path_filter,
            })
        self._add_to_routes(
            static_doc.serving_path, route_info, concrete=concrete,
            fingerprinted=static_doc.fingerprinted)

    def filter(self, filter_type, collection_paths=None, paths=None, locales=None, kinds=None):
        """Filter the routes based on the filter type and criteria."""
        # Convert paths to be regex.
        regex_paths = []
        for path in paths or []:
            regex_paths.append(re.compile(path))

        # Ability to specify a none locale using commanf flag.
        locales = locales or []
        if 'None' in locales:
            locales.append(None)

        if filter_type == 'whitelist':
            def _filter_whitelist(serving_path, route_info):
                # Check for whitelisted collection path.
                if collection_paths and 'collection_path' in route_info.meta:
                    if route_info.meta['collection_path'] in collection_paths:
                        return True

                # Check for whitelisted serving path.
                for regex_path in regex_paths:
                    if regex_path.match(serving_path):
                        return True

                # Check for whitelisted locale.
                if 'locale' in route_info.meta:
                    if route_info.meta['locale'] in locales:
                        return True

                # Check for whitelisted kind of routes.
                if kinds and route_info.kind in kinds:
                    return True

                # Not whitelist.
                return False

            count = self.routes.filter(_filter_whitelist)
            if count > 0:
                self.pod.logger.info('Whitelist filtered out {} routes.'.format(count))
        else:
            def _filter_blacklist(serving_path, route_info):
                # Check for blacklisted collection path.
                if collection_paths and 'collection_path' in route_info.meta:
                    if route_info.meta['collection_path'] in collection_paths:
                        return False

                # Check for blacklisted serving path.
                for regex_path in regex_paths:
                    if regex_path.match(serving_path):
                        return False

                # Check for blacklisted locale.
                if 'locale' in route_info.meta:
                    if route_info.meta['locale'] in locales:
                        return False

                # Check for blacklisted kinds of routes.
                if kinds and route_info.kind in kinds:
                    return False

                # Not blacklisted.
                return True

            count = self.routes.filter(_filter_blacklist)
            if count > 0:
                self.pod.logger.info('Blacklist filtered out {} routes.'.format(count))

    def from_cache(self, concrete=True):
        """Import routes from routes cache."""
        fingerprinted_dirs = set()
        for config in self.pod.static_configs:
            if 'fingerprinted' in config and config['fingerprinted']:
                fingerprinted_dirs.add(config['static_dir'])
        fingerprinted_dirs = tuple(fingerprinted_dirs)

        routes_data = self.pod.podcache.routes_cache.raw(
            concrete=concrete, env=self.pod.env.name)
        unchanged_pod_paths = set()
        removed_paths = []
        for key, item in routes_data.items():
            # For now ignore anything that doesn't have a hash.
            route_info = item['value']
            if not route_info.hashed:
                continue

            # Ignore deleted files.
            if not self.pod.file_exists(route_info.pod_path):
                removed_paths.append(key)
                continue

            # If the hash has changed then skip.
            if route_info.hashed != self.pod.hash_file(route_info.pod_path):
                continue

            # Ignore the fingerprinted files.
            if 'fingerprinted' in route_info.meta:
                if route_info.meta['fingerprinted']:
                    continue
                else:
                    # Check if the configuration has changed and the path should
                    # be fingerprinted.
                    if route_info.pod_path.startswith(fingerprinted_dirs):
                        continue

            unchanged_pod_paths.add(route_info.pod_path)
            self.routes.add(key, route_info, options=item['options'])

        for key in removed_paths:
            self.pod.podcache.routes_cache.remove(key, concrete=concrete)

        return unchanged_pod_paths

    def from_data(self, routes_data):
        """Import routes from data."""
        for key, item in routes_data.items():
            self.routes.add(
                key,
                RouteInfo.from_data(**item['value']),
                options=item['options'])

    def get_render_controller(self, path, route_info, params=None):
        """Find the correct render controller for the given route info."""
        return render_controller.RenderController.from_route_info(
            self.pod, path, route_info, params=params)

    def get_static_config_for_pod_path(self, pod_path):
        """Return the static configuration for a pod path."""
        text = '{} is not found in any static file configuration in the podspec.'
        if pod_path is None:
            raise MissingStaticConfigError(text.format(pod_path))

        for config in self.pod.static_configs:
            if config.get('dev') and not self.pod.env.dev:
                continue
            static_dirs = config.get('static_dirs')
            if not static_dirs:
                static_dirs = [config.get('static_dir')]
            if isinstance(static_dirs, str):
                static_dirs = [static_dirs]
            for static_dir in static_dirs:
                if pod_path.startswith(static_dir):
                    return config
            intl = config.get('localization', {})
            if intl:
                static_dirs = intl.get('static_dirs')
                if not static_dirs:
                    static_dirs = [intl.get('static_dir')]
                if isinstance(static_dirs, str):
                    static_dirs = [static_dirs]
                for static_dir in static_dirs:
                    if pod_path.startswith(static_dir):
                        return config

        raise MissingStaticConfigError(text.format(pod_path))

    def reconcile_documents(self, remove_docs=None, add_docs=None):
        """Remove old docs and add new docs to the routes."""
        for doc in remove_docs if remove_docs else []:
            self.routes.remove(doc.get_serving_path())
        for doc in add_docs if add_docs else []:
            self.add_doc(doc)

    def shard(self, shard_count, current_shard, attr='kind'):
        """Removes paths from the routes based on sharding rules."""
        self.routes.shard(shard_count, current_shard, attr=attr)

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

    def __init__(self, kind, pod_path=None, hashed=None, meta=None):
        self.kind = kind
        self.pod_path = pod_path
        self.hashed = hashed
        self.meta = meta or {}

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<RouteInfo kind={} meta={}>'.format(self.kind, self.meta)

    @classmethod
    def from_data(cls, kind, pod_path, hashed, meta):
        """Create the route info from data."""
        # Need to reconstruct the path filter object.
        if 'path_filter' in meta:
            meta['path_filter'] = grow_path_filter.PathFilter(
                ignored=meta['path_filter'].get('ignored'),
                included=meta['path_filter'].get('included'))
        if 'static_filter' in meta:
            meta['static_filter'] = grow_path_filter.PathFilter(
                ignored=meta['static_filter'].get('ignored'),
                included=meta['static_filter'].get('included'))
        return cls(kind, pod_path=pod_path, hashed=hashed, meta=meta)

    def export(self):
        """Export route information in a serializable format."""
        export_meta = {}
        for key in self.meta:
            meta_value = self.meta[key]
            if hasattr(meta_value, 'export'):
                meta_value = meta_value.export()
            export_meta[key] = meta_value
        return {
            'kind': self.kind,
            'pod_path': self.pod_path,
            'hashed': self.hashed,
            'meta': export_meta,
        }
