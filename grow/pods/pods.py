"""A pod encapsulates all files used to build a site."""

import copy
import atexit
import json
import logging
import os
import sys
import threading
import time
import shutil
import tempfile
import yaml
import jinja2
import progressbar
from werkzeug.contrib import cache as werkzeug_cache
from grow import storage as grow_storage
from grow.cache import podcache
from grow.collections import collection
from grow.common import extensions
from grow.common import features
from grow.common import logger
from grow.common import progressbar_non
from grow.common import utils
from grow.documents import document_fields
from grow.documents import static_document
from grow.extensions import extension_controller as ext_controller
from grow.partials import partials
from grow.performance import profile
from grow.preprocessors import preprocessors
from grow.rendering import rendered_document
from grow.rendering import renderer
from grow.rendering import render_pool as grow_render_pool
from grow.routing import path_filter as grow_path_filter
from grow.routing import path_format as grow_path_format
from grow.routing import router as grow_router
from grow.sdk import updater
from grow.templates import filters
from grow.templates import jinja_dependency
from grow.templates import tags
from grow.translations import catalog_holder
from grow.translations import locales
from grow.translations import translation_stats
from grow.translators import translators
from . import env as environment
from . import messages
from . import podspec
from . import routes as grow_routes
from . import static as grow_static


class Error(Exception):
    pass


class PodDoesNotExistError(Error, IOError):
    pass


# Pods can create temp directories. Need to track temp dirs for cleanup.
_POD_TEMP_DIRS = []


@atexit.register
def goodbye_pods():
    for tmp_dir in _POD_TEMP_DIRS:
        shutil.rmtree(tmp_dir, ignore_errors=True)


class Pod(object):
    """Grow pod."""
    # TODO(jeremydw): A handful of the properties of "pod" should be moved to the
    # "podspec" class.
    DEFAULT_EXTENSIONS_DIR_NAME = 'extensions'
    FEATURE_UI = 'ui'
    FEATURE_TRANSLATION_STATS = 'translation_stats'
    FILE_DEP_CACHE = '.depcache.json'
    FILE_PODSPEC = 'podspec.yaml'
    FILE_EXTENSIONS = 'extensions.txt'
    PATH_CONTROL = '/.grow/'

    def __eq__(self, other):
        return (isinstance(self, Pod)
                and isinstance(other, Pod)
                and self.root == other.root)

    def __init__(self, root, storage=grow_storage.AUTO, env=None, load_extensions=True, use_reroute=False):
        self._yaml = utils.SENTINEL
        self.storage = storage
        self.root = (root if self.storage.is_cloud_storage
                     else os.path.abspath(root))
        self.env = (env if env
                    else environment.Env(environment.EnvConfig(host='localhost')))
        self.locales = locales.Locales(pod=self)
        self.catalogs = catalog_holder.Catalogs(pod=self)
        # TODO: Remove the use_reroute when it is the only routing.
        self.use_reroute = use_reroute
        if not use_reroute:
            self.routes = grow_routes.Routes(pod=self)
        else:
            self.routes = None
        self._jinja_env_lock = threading.RLock()
        self._podcache = None
        self._features = features.Features(disabled=[
            self.FEATURE_TRANSLATION_STATS,
        ])

        self._extensions_controller = ext_controller.ExtensionController(self)

        # Modify sys.path for built-in extension support.
        if self.exists:
            _ext_dir = self.abs_path(self.extensions_dir)
            if os.path.exists(_ext_dir):
                sys.path.insert(0, _ext_dir)

        # Ensure preprocessors are loaded when pod is initialized.
        # Preprocessors may modify the environment in ways that are required by
        # data files (e.g. yaml constructors). Avoid loading extensions using
        # `load_extensions=False` to permit `grow install` to be used to
        # actually install extensions, prior to loading them.
        if load_extensions and self.exists:
            self.list_preprocessors()

        # Load extensions, ignore local extensions during install.
        self._load_extensions(load_extensions)

        try:
            update_checker = updater.Updater(self)
            update_checker.verify_required_version()
        except PodDoesNotExistError:
            pass  # Pod doesn't exist yet, simply pass.

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<Pod: {}>'.format(self.root)

    # DEPRECATED: Remove when no longer needed after re-route stable release.
    def _get_bytecode_cache(self):
        return self.jinja_bytecode_cache

    def _load_extensions(self, load_local_extensions=True):
        self._extensions_controller.register_builtins()

        if load_local_extensions and self.exists:
            self._extensions_controller.register_extensions(
                self.yaml.get('ext', []))

    def _normalize_path(self, pod_path):
        if '..' in pod_path:
            raise ValueError('.. not allowed in file paths.')
        return os.path.join(self.root, pod_path.lstrip('/'))

    def _normalize_pod_path(self, pod_path):
        if '..' in pod_path:
            raise ValueError('.. not allowed in pod paths.')
        if not pod_path.startswith('/'):
            pod_path = '/{}'.format(pod_path)
        return pod_path

    def _parse_object_cache_file(self):
        with self.profile.timer('Pod._parse_object_cache_file'):
            object_cache_file_name = '/{}'.format(podcache.FILE_OBJECT_CACHE)

            if not self.file_exists(object_cache_file_name):
                return {}
            try:
                return self.read_json(object_cache_file_name) or {}
            except IOError:
                path = self.abs_path(object_cache_file_name)
                raise podcache.PodCacheParseError(
                    'Error parsing: {}'.format(path))

    def _parse_dep_cache_file(self):
        with self.profile.timer('Pod._parse_dep_cache_file'):
            podcache_file_name = '/{}'.format(self.FILE_DEP_CACHE)

            # TODO Remove deprecated cachefile support.
            # Convert legacy yaml cache files.
            legacy_podcache_file_name = '/.podcache.yaml'
            if self.file_exists(legacy_podcache_file_name):
                logging.info(
                    'Converting {} to {}.'.format(legacy_podcache_file_name, podcache_file_name))
                # Do not use the utils.parse_yaml as that has extra constructors
                # that should not be run when the cache file is being parsed.
                temp_data = yaml.load(
                    self.read_file(legacy_podcache_file_name)) or {}
                if 'objects' in temp_data and temp_data['objects']:
                    object_cache_file_name = '/{}'.format(
                        podcache.FILE_OBJECT_CACHE)
                    self.write_file(object_cache_file_name,
                                    json.dumps(temp_data['objects']))
                self.delete_file(legacy_podcache_file_name)

            if not self.file_exists(podcache_file_name):
                return {}
            try:
                return self.read_json(podcache_file_name) or {}
            except IOError:
                path = self.abs_path(podcache_file_name)
                raise podcache.PodCacheParseError(
                    'Error parsing: {}'.format(path))

    @utils.memoize
    def _parse_yaml(self):
        podspec_file_name = '/{}'.format(self.FILE_PODSPEC)
        try:
            return utils.parse_yaml(self.read_file(podspec_file_name))
        except IOError as e:
            path = self.abs_path(podspec_file_name)
            if e.args[0] == 2 and e.filename:
                raise PodDoesNotExistError('Pod not found in: {}'.format(path))
            raise podspec.PodSpecParseError('Error parsing: {}'.format(path))

    def set_env(self, env):
        if not isinstance(env, environment.Env):
            env = environment.Env(env)
        if env and env.name:
            untag = document_fields.DocumentFields.untag
            content = untag(self._parse_yaml(), params={'env': env.name})
            self._yaml = content
            # Preprocessors may depend on env, reset cache.
            # pylint: disable=no-member
            self.list_preprocessors.reset()
            self.podcache.reset()
        self.env = env

    @utils.cached_property
    def cache(self):
        if utils.is_appengine():
            return werkzeug_cache.MemcachedCache(default_timeout=0)
        return werkzeug_cache.SimpleCache(default_timeout=0)

    @property
    def error_routes(self):
        return self.yaml.get('error_routes')

    @property
    def exists(self):
        return self.file_exists('/{}'.format(self.FILE_PODSPEC))

    @property
    def extensions_controller(self):
        return self._extensions_controller

    @property
    def grow_version(self):
        return self.podspec.grow_version

    @utils.cached_property
    def jinja_bytecode_cache(self):
        return jinja2.MemcachedBytecodeCache(client=self.cache)

    @property
    def logger(self):
        return logger.LOGGER

    @utils.cached_property
    def partials(self):
        """Returns the pod partials object."""
        return partials.Partials(self)

    @utils.cached_property
    def path_filter(self):
        """Filter for testing path formats."""
        if self.env.name == environment.Name.DEV or self.env.name is None:
            filter_config = self.yaml.get('filter', {})
        else:
            if 'deployments' not in self.yaml:
                raise ValueError('No pod-specific deployments configured.')
            filter_config = (self.yaml['deployments']
                             .get(self.env.name, {})
                             .get('filter', {}))
        return grow_path_filter.PathFilter(
            filter_config.get('ignore_paths'), filter_config.get('include_paths'))

    @utils.cached_property
    def path_format(self):
        """Format utility for url paths."""
        return grow_path_format.PathFormat(self)

    @property
    def podcache(self):
        if not self._podcache:
            self._podcache = podcache.PodCache(
                dep_cache=self._parse_dep_cache_file(),
                obj_cache=self._parse_object_cache_file(),
                pod=self)
        return self._podcache

    @property
    def podspec(self):
        return podspec.PodSpec(yaml=self.yaml, pod=self)

    @utils.cached_property
    def profile(self):
        """Profile object for code timing."""
        return profile.Profile()

    @utils.cached_property
    def render_pool(self):
        """Render pool rendering documents."""
        return grow_render_pool.RenderPool(self)

    @utils.cached_property
    def router(self):
        """Router object for routing."""
        return grow_router.Router(self)

    @property
    def static_configs(self):
        """Yields each of the static configurations."""
        podspec_config = self.podspec.get_config()
        if 'static_dirs' not in podspec_config:
            return
        for config in podspec_config['static_dirs']:
            yield config

    @utils.cached_property
    def tmp_dir(self):
        """Temp directory for temporary file caching."""
        dir_name = tempfile.mkdtemp()
        _POD_TEMP_DIRS.append(dir_name)
        return dir_name

    @property
    def title(self):
        return self.yaml.get('title')

    @utils.cached_property
    def translation_stats(self):
        return translation_stats.TranslationStats()

    @property
    def extensions_dir(self):
        return self.yaml.get('extensions_dir', Pod.DEFAULT_EXTENSIONS_DIR_NAME)

    @property
    def ui(self):
        if self.env.name == environment.Name.DEV or self.env.name is None:
            ui_config = self.yaml.get('ui')
        else:
            if 'deployments' not in self.yaml:
                raise ValueError('No pod-specific deployments configured.')
            ui_config = (self.yaml['deployments']
                         .get(self.env.name, {})
                         .get('ui'))
        return ui_config

    @property
    def yaml(self):
        if self._yaml is utils.SENTINEL:
            self._yaml = self._parse_yaml() or {}
        return self._yaml

    def abs_path(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return os.path.join(self.root, path)

    def create_collection(self, collection_path, fields):
        pod_path = os.path.join(
            collection.Collection.CONTENT_PATH, collection_path)
        return collection.Collection.create(pod_path, fields, pod=self)

    def delete(self):
        """Deletes the pod by deleting all of its files."""
        pod_paths = self.list_dir('/')
        for path in pod_paths:
            self.delete_file(path)
        return pod_paths

    def delete_file(self, pod_path):
        path = self._normalize_path(pod_path)
        return self.storage.delete(path)

    def delete_files(self, pod_paths, recursive=False, pattern=None):
        """Delete matching files from the pod_paths."""
        normal_paths = []
        for pod_path in pod_paths:
            normal_paths.append(self._normalize_path(pod_path))
        return self.storage.delete_files(normal_paths, recursive=recursive, pattern=pattern)

    def determine_paths_to_build(self, pod_paths=None):
        """Determines which paths are going to be built with optional path filtering."""
        if pod_paths:
            # When provided a list of pod_paths do a custom routing tree based on
            # the docs that are dependent based on the dependecy graph.
            def _gen_docs(pod_paths):
                for pod_path in pod_paths:
                    for dep_path in self.podcache.dependency_graph.match_dependents(
                            self._normalize_pod_path(pod_path)):
                        yield self.get_doc(dep_path)
            routes = grow_routes.Routes.from_docs(self, _gen_docs(pod_paths))
        else:
            routes = self.get_routes()
        paths = []
        for items in routes.get_locales_to_paths().values():
            paths += items
        return paths, routes

    def disable(self, feature):
        """Disable a grow feature."""
        self._features.disable(feature)

    def dump(self, suffix='index.html', append_slashes=True, pod_paths=None, use_threading=True):
        """Dumps the pod, yielding rendered_doc based on pod routes."""
        for rendered_doc in self.export(
                suffix=suffix, append_slashes=append_slashes, pod_paths=pod_paths,
                use_threading=use_threading):
            yield rendered_doc
        if self.ui and self.is_enabled(self.FEATURE_UI):
            for rendered_doc in self.export_ui():
                yield rendered_doc

    def enable(self, feature):
        """Enable a grow feature."""
        self._features.enable(feature)

    def export(self, suffix=None, append_slashes=False, pod_paths=None, use_threading=True):
        """Builds the pod, yielding rendered_doc based on pod routes."""
        if self.use_reroute:
            for rendered_doc in renderer.Renderer.rendered_docs(
                    self, self.router.routes, use_threading=use_threading):
                yield rendered_doc
        else:
            paths, routes = self.determine_paths_to_build(pod_paths=pod_paths)
            for rendered_doc in self.render_paths(
                    paths, routes, suffix=suffix, append_slashes=append_slashes):
                yield rendered_doc
            if not pod_paths:
                error_controller = routes.match_error('/404.html')
                if error_controller:
                    yield rendered_document.RenderedDocument(
                        '/404.html', error_controller.render({}), tmp_dir=self.tmp_dir)

    def export_ui(self):
        """Builds the grow ui tools, returning a mapping of paths to content."""
        paths = []
        source_prefix = 'node_modules/'
        destination_root = '_grow/ui/'
        tools_dir = 'tools/'
        tool_prefix = 'grow-tool-'

        # Add the base ui files.
        source_root = os.path.join(utils.get_grow_dir(), 'ui', 'dist')
        for path in ['css/ui.min.css', 'js/ui.min.js']:
            source_path = os.path.join(source_root, path)
            output_path = os.sep + os.path.join(destination_root, path)
            yield rendered_document.RenderedDocument(
                output_path, self.storage.read(source_path))

        # Add the files from each of the tools.
        for tool in self.ui.get('tools', []):
            tool_path = '{}{}{}'.format(
                source_prefix, tool_prefix, tool['kind'])
            for root, dirs, files in self.walk(tool_path):
                for directory in dirs:
                    if directory.startswith('.'):
                        dirs.remove(directory)
                pod_dir = root.replace(self.root, '')
                for file_name in files:
                    paths.append(os.path.join(pod_dir, file_name))

        text = 'Building UI Tools: %(value)d/{} (in %(time_elapsed).9s)'
        widgets = [progressbar.FormatLabel(text.format(len(paths)))]
        progress = progressbar_non.create_progressbar(
            "Building UI Tools...", widgets=widgets, max_value=len(paths))
        progress.start()
        for path in paths:
            output_path = path.replace(
                source_prefix, '{}{}'.format(destination_root, tools_dir))
            yield rendered_document.RenderedDocument(
                output_path, self.read_file(path))
            progress.update(progress.value + 1)
        progress.finish()

    def file_exists(self, pod_path):
        path = self._normalize_path(pod_path)
        return self.storage.exists(path)

    def file_modified(self, pod_path):
        path = self._normalize_path(pod_path)
        return self.storage.modified(path)

    def file_size(self, pod_path):
        path = self._normalize_path(pod_path)
        return self.storage.size(path)

    def get_catalogs(self, template_path=None):
        return catalog_holder.Catalogs(pod=self, template_path=template_path)

    def get_collection(self, collection_path):
        """Returns a collection.

        Args:
          collection_path: A collection's path relative to the /content/ directory.
        Returns:
          Collection.
        """
        pod_path = os.path.join(
            collection.Collection.CONTENT_PATH, collection_path)
        cached = self.podcache.collection_cache.get_collection(pod_path)
        if cached:
            return cached

        col = collection.Collection.get(pod_path, _pod=self)
        self.podcache.collection_cache.add_collection(col)
        return col

    def get_deployment(self, nickname):
        """Returns a pod-specific deployment."""
        # Lazy import avoids environment errors and speeds up importing.
        from grow.deployments import deployments
        if 'deployments' not in self.yaml:
            raise ValueError('No pod-specific deployments configured.')
        destination_configs = self.yaml['deployments']
        if nickname not in destination_configs:
            text = 'No deployment named {}. Valid deployments: {}.'
            keys = ', '.join(destination_configs.keys())
            raise ValueError(text.format(nickname, keys))
        deployment_params = destination_configs[nickname]
        kind = deployment_params.pop('destination')
        try:
            config = destination_configs[nickname]
            deployment = deployments.make_deployment(
                kind, config, name=nickname)
        except TypeError:
            logging.exception('Invalid deployment parameters.')
            raise
        deployment.pod = self
        return deployment

    def get_doc(self, pod_path, locale=None):
        """Returns a document, given the document's pod path."""
        collection_path, unused_path = os.path.split(pod_path)
        if not collection_path or not unused_path:
            text = '"{}" is not a path to a document.'.format(pod_path)
            raise collection.BadCollectionNameError(text)
        original_collection_path = collection_path
        col = self.get_collection(collection_path)
        while not col.exists:
            col = col.parent
            if not col:
                col = self.get_collection(original_collection_path)
                break
        return col.get_doc(pod_path, locale=locale)

    def get_home_doc(self):
        home = self.yaml.get('home')
        if home is None:
            return None
        return self.get_doc(home)

    @utils.memoize
    def get_jinja_env(self, locale='', root=None):
        with self._jinja_env_lock:
            kwargs = {
                'autoescape': True,
                'extensions': [
                    'jinja2.ext.autoescape',
                    'jinja2.ext.do',
                    'jinja2.ext.i18n',
                    'jinja2.ext.loopcontrols',
                    'jinja2.ext.with_',
                ],
                'loader': self.storage.JinjaLoader(self.root if root is None else root),
                'lstrip_blocks': True,
                'trim_blocks': True,
            }
            if self.env.cached:
                kwargs['bytecode_cache'] = self._get_bytecode_cache()
            kwargs['extensions'].extend(self.list_jinja_extensions())
            env = jinja_dependency.DepEnvironment(**kwargs)
            env.filters.update(filters.create_builtin_filters())
            env.globals.update(
                **tags.create_builtin_globals(env, self, locale=locale))
            return env

    def get_routes(self):
        return self.routes

    def get_static(self, pod_path, locale=None):
        """Returns a StaticFile, given the static file's pod path."""
        if self.use_reroute:
            document = static_document.StaticDocument(
                self, pod_path, locale=locale)
            if document.exists:
                return document
        else:
            for route in self.routes.static_routing_map.iter_rules():
                controller = route.endpoint
                if controller.KIND == messages.Kind.STATIC:
                    serving_path = controller.match_pod_path(pod_path)
                    if serving_path:
                        return grow_static.StaticFile(
                            pod_path, serving_path, locale=locale, pod=self,
                            controller=controller, fingerprinted=controller.fingerprinted,
                            localization=controller.localization)
        text = ('Either no file exists at "{}" or the "static_dirs" setting was '
                'not configured for this path in {}.'.format(
                    pod_path, self.FILE_PODSPEC))
        raise grow_static.BadStaticFileError(text)

    def get_podspec(self):
        return self.podspec

    @utils.memoize
    def get_translator(self, service=utils.SENTINEL):
        if 'translators' not in self.yaml:
            return None
        if ('services' not in self.yaml['translators']
                or not self.yaml['translators']['services']):
            return None
        translator_config = self.yaml['translators']
        inject_name = translator_config.get('inject')
        translators.register_extensions(
            self.yaml.get('extensions', {}).get('translators', []),
            self.root,
        )
        translator_services = copy.deepcopy(translator_config['services'])
        if service is not utils.SENTINEL:
            valid_service_kinds = [each['service']
                                   for each in translator_services]
            if not valid_service_kinds:
                text = 'Missing required "service" field in translator config.'
                raise ValueError(text)
            if service not in valid_service_kinds and service is not None:
                text = 'No translator service "{}". Valid services: {}.'
                keys = ', '.join(valid_service_kinds)
                raise ValueError(text.format(service, keys))
        else:
            # Use the first configured translator by default.
            translator_services = translator_services[:1]
        for service_config in translator_services:
            if service_config.get('service') == service or len(translator_services) == 1:
                translator_kind = service_config.pop('service')
                inject = inject_name == translator_kind
                return translators.create_translator(
                    self, translator_kind, service_config,
                    inject=inject,
                    project_title=translator_config.get('project_title'),
                    instructions=translator_config.get('instructions'))
        raise ValueError('No translator service found: {}'.format(service))

    def get_url(self, pod_path, locale=None):
        if pod_path.startswith('/content'):
            doc = self.get_doc(pod_path, locale=locale)
            return doc.url
        static = self.get_static(pod_path, locale=locale)
        return static.url

    def inject_preprocessors(self, doc=None, collection=None):
        """Conditionally injects or creates data from preprocessors. If a doc
        is provided, preprocessors inject data to doc fields. If a collection
        is provided, the first matching preprocessor returns a list of docs."""
        for preprocessor in self.list_preprocessors():
            if doc is not None:
                if preprocessor.can_inject(doc=doc):
                    preprocessor.inject(doc=doc)
                    return preprocessor
            if collection is not None:
                if preprocessor.can_inject(collection=collection):
                    preprocessor.inject(collection=collection)
                    return preprocessor

    def inject_translators(self, doc):
        translator = self.get_translator()
        if not translator:
            return
        translator.inject(doc=doc)
        return translator

    def is_enabled(self, feature):
        return self._features.is_enabled(feature)

    def list_collections(self, paths=None):
        cols = collection.Collection.list(self)
        if paths:
            return [col for col in cols if col.collection_path in paths]
        return cols

    def list_deployments(self):
        destination_configs = self.yaml['deployments']
        results = []
        for name in destination_configs.keys():
            results.append(self.get_deployment(name))
        return results

    def list_dir(self, pod_path='/', recursive=True):
        path = self._normalize_path(pod_path)
        return self.storage.listdir(path, recursive=recursive)

    def list_jinja_extensions(self):
        loaded_extensions = []
        for name in self.yaml.get('extensions', {}).get('jinja2', []):
            try:
                value = extensions.import_extension(name, [self.root])
            except ImportError:
                logging.error(
                    'Error importing %s. Module path must be relative to '
                    'the pod root.', repr(name))
                raise
            loaded_extensions.append(value)
        return loaded_extensions

    def list_locales(self):
        codes = self.yaml.get('localization', {}).get('locales', [])
        return locales.Locale.parse_codes(codes)

    @utils.memoize
    def list_preprocessors(self):
        results = []
        preprocessors.register_extensions(
            self.yaml.get('extensions', {}).get('preprocessors', []),
            self.root,
        )
        preprocessor_config = copy.deepcopy(self.yaml.get('preprocessors', []))
        for params in preprocessor_config:
            kind = params.pop('kind')
            try:
                preprocessor = preprocessors.make_preprocessor(kind, params, self)
                results.append(preprocessor)
            except ValueError as err:
                # New extensions will not show up here.
                self.logger.info(err)
        return results

    def list_statics(self, pod_path, locale=None, include_hidden=False):
        for path in self.list_dir(pod_path):
            if include_hidden or not path.rsplit(os.sep, 1)[-1].startswith('.'):
                yield self.get_static(pod_path + path, locale=locale)

    def load(self):
        if self.routes:
            self.routes.routing_map

    def match(self, path):
        return self.routes.match(path, env=self.env.to_wsgi_env())

    def move_file_to(self, source_pod_path, destination_pod_path):
        source_path = self._normalize_path(source_pod_path)
        dest_path = self._normalize_path(destination_pod_path)
        return self.storage.move_to(source_path, dest_path)

    def normalize_locale(self, locale, default=None):
        locale = locale or default or self.podspec.default_locale
        if isinstance(locale, basestring):
            try:
                locale = locales.Locale.parse(locale)
            except ValueError as err:
                # Locale could be an alias.
                locale = locales.Locale.from_alias(self, locale)
        if locale is not None:
            locale.set_alias(self)
        return locale

    def open_file(self, pod_path, mode=None):
        path = self._normalize_path(pod_path)
        return self.storage.open(path, mode=mode)

    def preprocess(self, preprocessor_names=None, run_all=False, tags=None,
                   build=True, ratelimit=None):
        if not preprocessor_names:
            self.catalogs.compile()  # Preprocess translations.

        # Extension support for preprocessors.
        preprocessors = self.yaml.get('preprocessors', [])
        for config in preprocessors:
            self.extensions_controller.trigger(
                'preprocess', config, preprocessor_names, tags, run_all, ratelimit)

        # Legacy support for preprocessors.
        # TODO Remove when not supporting the legacy preprocessors.
        for preprocessor in self.list_preprocessors():
            if preprocessor_names:
                if preprocessor.name in preprocessor_names:
                    preprocessor.run(build=build)
            elif tags:
                if set(preprocessor.tags).intersection(tags):
                    preprocessor.run(build=build)
            elif preprocessor.autorun or run_all:
                preprocessor.run(build=build)
            if ratelimit:
                time.sleep(ratelimit)

    def read_csv(self, path, locale=utils.SENTINEL):
        with self.profile.timer('Pod.read_csv', label=path, meta={'path': path}):
            return utils.get_rows_from_csv(pod=self, path=path, locale=locale)

    def read_file(self, pod_path):
        path = self._normalize_path(pod_path)
        with self.profile.timer('Pod.read_file', label=path, meta={'path': path}):
            return self.storage.read(path)

    def read_json(self, path):
        """Read and parse a json file."""
        with self.open_file(path, 'r') as json_file:
            return json.load(json_file)

    def read_yaml(self, path, locale=None):
        """Read, parse, and untag a yaml file."""
        contents = self.podcache.file_cache.get(path, locale=locale)
        if contents is None:
            label = '{} ({})'.format(path, locale)
            meta = {'path': path, 'locale': locale}
            with self.profile.timer('Pod.read_yaml', label=label, meta=meta):
                fields = self.podcache.file_cache.get(path, locale='__raw__')
                if fields is None:
                    fields = utils.parse_yaml(
                        self.read_file(path), pod=self, locale=locale)
                    self.podcache.file_cache.add(
                        path, fields, locale='__raw__')
                try:
                    contents = document_fields.DocumentFields.untag(
                        fields, locale=locale, params={'env': self.env.name})
                    self.podcache.file_cache.add(path, contents, locale=locale)
                except Exception:
                    logging.error('Error parsing -> {}'.format(path))
                    raise
        return contents

    def render_paths(self, paths, routes, suffix=None, append_slashes=False):
        """Renders the given paths and yields each path and content."""
        text = 'Building: %(value)d/{} (in %(time_elapsed).9s)'
        widgets = [progressbar.FormatLabel(text.format(len(paths)))]
        bar = progressbar_non.create_progressbar(
            "Building pod...", widgets=widgets, max_value=len(paths))
        bar.start()
        for path in paths:
            output_path = path
            controller, params = routes.match(
                path, env=self.env.to_wsgi_env())
            # Append a suffix onto rendered routes only. This supports dumping
            # paths that would serve at URLs that terminate in "/" or without
            # an extension to an HTML file suitable for writing to a
            # filesystem. Static routes and other routes that may export to
            # paths without extensions should remain unmodified.
            if suffix and controller.KIND == messages.Kind.RENDERED:
                if (append_slashes and not output_path.endswith('/')
                        and not os.path.splitext(output_path)[-1]):
                    output_path = output_path.rstrip('/') + '/'
                if append_slashes and output_path.endswith('/') and suffix:
                    output_path += suffix
            try:
                key = 'Pod.render_paths.render'
                if isinstance(controller, grow_static.StaticController):
                    key = 'Pod.render_paths.render.static'

                with self.profile.timer(key, label=output_path, meta={'path': output_path}):
                    yield rendered_document.RenderedDocument(
                        output_path, controller.render(params, inject=False),
                        tmp_dir=self.tmp_dir)
            except:
                self.logger.error('Error building: {}'.format(controller))
                raise
            bar.update(bar.value + 1)
        bar.finish()

    def reset_yaml(self):
        # Tell the cached property to reset.
        # pylint: disable=no-member
        self._parse_yaml.reset()

    def to_message(self):
        message = messages.PodMessage()
        message.collections = [collection.to_message()
                               for collection in self.list_collections()]
        message.routes = self.routes.to_message()
        return message

    def walk(self, pod_path):
        path = self._normalize_path(pod_path)
        return self.storage.walk(path)

    def write_file(self, pod_path, content):
        with self.profile.timer(
                'Pod.write_file', label=pod_path, meta={'path': pod_path}):
            self.podcache.file_cache.remove(pod_path)
            path = self._normalize_path(pod_path)
            self.storage.write(path, content)

    def write_yaml(self, path, content):
        with self.profile.timer(
                'Pod.write_yaml', label=path, meta={'path': path}):
            self.podcache.collection_cache.remove_by_path(path)
            self.podcache.document_cache.remove_by_path(path)
            content = utils.dump_yaml(content)
            self.write_file(path, content)
