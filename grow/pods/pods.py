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
import cachelib
from grow import storage as grow_storage
from grow.cache import podcache
from grow.collections import collection
from grow.common import deprecated
from grow.common import features
from grow.common import logger
from grow.common import progressbar_non
from grow.common import untag
from grow.common import utils
from grow.documents import static_document
from grow.extensions import extension_controller as ext_controller
from grow.extensions import extension_importer
from grow.partials import partials
from grow.performance import profile
from grow.pods import errors
from grow.preprocessors import preprocessors
from grow.rendering import markdown_utils
from grow.rendering import rendered_document
from grow.rendering import renderer
from grow.rendering import render_pool as grow_render_pool
from grow.routing import path_filter as grow_path_filter
from grow.routing import path_format as grow_path_format
from grow.routing import router as grow_router
from grow.templates import filters
from grow.templates import jinja_dependency
from grow.templates import tags
from grow.translations import catalog_holder
from grow.translations import locales
from grow.translations import translation_stats
from grow.translators import translators
from . import env as environment
from . import podspec


class Error(Exception):

    def __init__(self, message):
        super(Error, self).__init__(message)
        self.message = message


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
    INSTALLED_EXTENSIONS_DIR_PATH = 'extensions'
    LOCAL_EXTENSIONS_DIR_PATH = 'ext'
    FEATURE_UI = 'ui'
    FEATURE_TRANSLATION_STATS = 'translation_stats'
    FEATURE_OLD_SLUGIFY = 'legacy_slugify'
    FILE_DEP_CACHE = 'depcache.json'
    FILE_PODSPEC = 'podspec.yaml'
    FILE_EXTENSIONS = 'extensions.txt'
    PATH_CONTROL = '/.grow/'

    def __eq__(self, other):
        return (isinstance(self, Pod)
                and isinstance(other, Pod)
                and self.root == other.root)

    def __init__(self, root, storage=grow_storage.AUTO, env=None, load_extensions=True):
        self.deprecated = deprecated.DeprecationManager(self.logger.warn)
        self._yaml = utils.SENTINEL
        self.storage = storage
        self.root = (root if self.storage.is_cloud_storage
                     else os.path.abspath(root))
        self.env = (env if env
                    else environment.Env(environment.EnvConfig(host='localhost')))
        self.locales = locales.Locales(pod=self)
        self.catalogs = catalog_holder.Catalogs(pod=self)
        self._jinja_env_lock = threading.RLock()
        self._podcache = None
        self._features = features.Features(disabled=[
            self.FEATURE_TRANSLATION_STATS,
            self.FEATURE_OLD_SLUGIFY,
        ])
        self._experiments = features.Features(default_enabled=False)

        self._extensions_controller = ext_controller.ExtensionController(self)

        if self.exists:
            # Modify sys.path for built-in extension support.
            _installed_ext_dir = self.abs_path(self.extensions_dir)
            if os.path.exists(_installed_ext_dir):
                sys.path.insert(0, _installed_ext_dir)

            # Modify sys.path for local extension support.
            _local_ext_dir = self.abs_path(Pod.LOCAL_EXTENSIONS_DIR_PATH)
            if os.path.exists(_local_ext_dir):
                sys.path.insert(0, _local_ext_dir)

            # Load the features from the podspec.
            self._load_features()

            # Load the experiments from the podspec.
            self._load_experiments()

        # Ensure preprocessors are loaded when pod is initialized.
        # Preprocessors may modify the environment in ways that are required by
        # data files (e.g. yaml constructors). Avoid loading extensions using
        # `load_extensions=False` to permit `grow install` to be used to
        # actually install extensions, prior to loading them.
        if load_extensions and self.exists:
            self.list_preprocessors()

        # Load extensions, ignore local extensions during install.
        self._load_extensions(load_extensions)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<Pod: {}>'.format(self.root)

    # DEPRECATED: Remove when no longer needed after re-route stable release.
    def _get_bytecode_cache(self):
        return self.jinja_bytecode_cache

    def _load_experiments(self):
        config = self.yaml.get('experiments', {})
        for key, value in config.items():
            # Expertiments can be turned on with a True value,
            # be turned off with a False value,
            # or turned on by a providing configuration value.
            if value is True:
                self._experiments.enable(key)
            elif value is False:
                self._experiments.disable(key)
            else:
                self._experiments.enable(key, config=value)

    def _load_extensions(self, load_local_extensions=True):
        self._extensions_controller.register_builtins()

        if load_local_extensions and self.exists:
            self._extensions_controller.register_extensions(
                self.yaml.get('ext', []))

    def _load_features(self):
        config = self.yaml.get('features', {})
        for key, value in config.items():
            # Features can be turned on with a True value,
            # be turned off with a False value,
            # or turned on by a providing configuration value.
            if value is True:
                self._features.enable(key)
            elif value is False:
                self._features.disable(key)
            else:
                self._features.enable(key, config=value)

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

    def _parse_routes_cache_file(self):
        with self.profile.timer('Pod._parse_routes_cache_file'):
            routes_cache_file_name = '{}{}'.format(
                self.PATH_CONTROL, podcache.FILE_ROUTES_CACHE)
            if not self.file_exists(routes_cache_file_name):
                return {}
            try:
                return self.read_json(routes_cache_file_name) or {}
            except ValueError:
                # File became corrupted; delete it and start over.
                # https://github.com/grow/grow/issues/1050#issuecomment-596346032
                self.delete_file(routes_cache_file_name)
                return {}
            except IOError:
                path = self.abs_path(routes_cache_file_name)
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

    @staticmethod
    def clean_pod_path(pod_path):
        """Cleanup the pod path."""
        if not pod_path.startswith('/'):
            pod_path = '/{}'.format(pod_path)
        return pod_path

    def set_env(self, env):
        if not isinstance(env, environment.Env):
            env = environment.Env(env)
        if env and env.name:
            content = untag.Untag.untag(self._parse_yaml(), params={
                'env': untag.UntagParamRegex(env.name),
            })
            self._yaml = content
            # Preprocessors may depend on env, reset cache.
            # pylint: disable=no-member
            self.list_preprocessors.reset()
            self.podcache.reset()
            # Need to reload the extension configs for changes based on env.
            self._extensions_controller.update_extension_configs(
                self.yaml.get('ext', []))
        self.env = env

    @utils.cached_property
    def cache(self):
        return cachelib.SimpleCache(default_timeout=0)

    @property
    def error_routes(self):
        return self.yaml.get('error_routes')

    @property
    def exists(self):
        return self.file_exists('/{}'.format(self.FILE_PODSPEC))

    @property
    def experiments(self):
        return self._experiments

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

    @property
    def markdown(self):
        """Markdown processor with pod flavored markdown."""
        # Do not cached property, causes issue with extensions.
        return self.markdown_util.markdown

    @utils.cached_property
    def markdown_util(self):
        """Markdown util specific to pod flavored markdown."""
        return markdown_utils.MarkdownUtil(self)

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
                routes_cache=self._parse_routes_cache_file(),
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

        # Allow for extensions to create static directory configs.
        hook_static_dirs = self.extensions_controller.trigger('static_dir')
        for config in hook_static_dirs:
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
        return self.yaml.get('extensions_dir', Pod.INSTALLED_EXTENSIONS_DIR_PATH)

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

    def copy_file_to(self, source_pod_path, destination_pod_path):
        source_path = self._normalize_path(source_pod_path)
        dest_path = self._normalize_path(destination_pod_path)
        return self.storage.copy_to(source_path, dest_path)

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

    def disable(self, feature):
        """Disable a grow feature."""
        self._features.disable(feature)

    def dump(self, suffix='index.html', append_slashes=True, pod_paths=None,
             use_threading=True, source_dir=None):
        """Dumps the pod, yielding rendered_doc based on pod routes."""
        for rendered_doc in self.export(
                suffix=suffix, append_slashes=append_slashes, pod_paths=pod_paths,
                use_threading=use_threading, source_dir=source_dir):
            yield rendered_doc
        if self.ui and self.is_enabled(self.FEATURE_UI):
            for rendered_doc in self.export_ui():
                yield rendered_doc

    def enable(self, feature):
        """Enable a grow feature."""
        self._features.enable(feature)

    def export(self, suffix=None, append_slashes=False, pod_paths=None,
               use_threading=True, source_dir=None):
        """Builds the pod, yielding rendered_doc based on pod routes."""
        for rendered_doc in renderer.Renderer.rendered_docs(
                self, self.router.routes, use_threading=use_threading,
                source_dir=source_dir):
            yield rendered_doc

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
        from grow.deployments import deployments as grow_deployments
        if 'deployments' not in self.yaml:
            raise ValueError('No pod-specific deployments configured.')
        destination_configs = self.yaml['deployments']
        if nickname not in destination_configs:
            text = 'No deployment named {}. Valid deployments: {}.'
            keys = ', '.join(list(destination_configs.keys()))
            raise ValueError(text.format(nickname, keys))
        deployment_params = destination_configs[nickname]
        kind = deployment_params.pop('destination')
        try:
            config = destination_configs[nickname]
            deployments = grow_deployments.Deployments()
            self.extensions_controller.trigger(
                'deployment_register', deployments)
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
        doc = col.get_doc(pod_path, locale=locale)
        return doc

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
            env.filters.update(filters.create_builtin_filters(env, self, locale=locale))
            env.globals.update(
                **tags.create_builtin_globals(env, self, locale=locale))
            return env

    def get_static(self, pod_path, locale=None):
        """Returns a StaticFile, given the static file's pod path."""
        document = static_document.StaticDocument(
            self, pod_path, locale=locale)
        if document.exists:
            return document

        text = ('Either no file exists at "{}" or the "static_dirs" setting was '
                'not configured for this path in {}.'.format(
                    pod_path, self.FILE_PODSPEC))
        raise errors.DocumentDoesNotExistError(text)

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
        translator_extensions = self.yaml.get(
            'extensions', {}).get('translators', [])
        translators.register_extensions(
            translator_extensions,
            self.root,
        )

        # TODO: Show deprecation message in the future.
        # if translator_extensions:
        #     legacy_message = 'Legacy translators are deprecated and will be removed in the future: {}'
        #     self.deprecated(
        #         'legacy_translator',
        #         legacy_message.format(', '.join(translator_extensions)),
        #         url='https://grow.dev/migration/1.0.0')

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
                return translators.create_translator(
                    self, translator_kind, service_config,
                    project_title=translator_config.get('project_title'),
                    instructions=translator_config.get('instructions'))
        raise ValueError('No translator service found: {}'.format(service))

    def get_url(self, pod_path, locale=None):
        if pod_path.startswith('/content'):
            doc = self.get_doc(pod_path, locale=locale)
        else:
            doc = self.get_static(pod_path, locale=locale)

        if not doc.exists:
            raise errors.DocumentDoesNotExistError(
                'Referenced document does not exist: {}'.format(pod_path))
        return doc.url

    def hash_file(self, pod_path):
        """Provide the hash of the file from the storage."""
        path = self._normalize_path(pod_path)
        with self.profile.timer('Pod.hash_file', label=path, meta={'path': path}):
            return self.storage.hash(path)

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
        jinja_extensions = self.yaml.get('extensions', {}).get('jinja2', [])
        for name in jinja_extensions:
            try:
                value = extension_importer.ExtensionImporter.find_extension(
                    name, self.root)
            except ImportError:
                logging.error(
                    'Error importing %s. Module path must be relative to '
                    'the pod root.', repr(name))
                raise
            loaded_extensions.append(value)

        # TODO: Show deprecation message in the future.
        # if jinja_extensions:
        #     legacy_message = 'Legacy jinja2 extensions are deprecated and will be removed in the future: {}'
        #     self.deprecated(
        #         'legacy_jinja2',
        #         legacy_message.format(', '.join(jinja_extensions)),
        #         url='https://grow.dev/migration/1.0.0')

        loaded_extensions.extend(
            self.extensions_controller.trigger('jinja_extensions'))
        return loaded_extensions

    def list_locales(self):
        codes = self.yaml.get('localization', {}).get('locales', [])
        return self.normalize_locales(locales.Locale.parse_codes(codes))

    @utils.memoize
    def list_preprocessors(self):
        results = []
        preprocessors.register_extensions(
            self.yaml.get('extensions', {}).get('preprocessors', []),
            self.root,
        )
        preprocessor_config = copy.deepcopy(self.yaml.get('preprocessors', []))
        legacy_preprocessors = []
        for params in preprocessor_config:
            kind = params.pop('kind')
            legacy_preprocessors.append(kind)

            try:
                preprocessor = preprocessors.make_preprocessor(
                    kind, params, self)
                results.append(preprocessor)
            except ValueError as err:
                # New extensions don't exists and are considered a value error.
                pass

        # TODO: Show deprecation message in the future.
        # if legacy_preprocessors:
        #     legacy_message = 'Legacy preprocessors are deprecated and will be removed in the future: {}'
        #     self.deprecated(
        #         'legacy_preprocessors',
        #         legacy_message.format(', '.join(legacy_preprocessors)),
        #         url='https://grow.dev/migration/1.0.0')

        return results

    def list_statics(self, pod_path, locale=None, include_hidden=False):
        for path in self.list_dir(pod_path):
            if include_hidden or not path.rsplit(os.sep, 1)[-1].startswith('.'):
                yield self.get_static(pod_path + path, locale=locale)

    def match(self, path):
        return self.router.routes.match(path)

    def move_file_to(self, source_pod_path, destination_pod_path):
        source_path = self._normalize_path(source_pod_path)
        dest_path = self._normalize_path(destination_pod_path)
        return self.storage.move_to(source_path, dest_path)

    def normalize_locale(self, locale, default=None):
        locale = locale or default or self.podspec.default_locale
        if isinstance(locale, str):
            try:
                locale = locales.Locale.parse(locale)
            except ValueError as err:
                # Locale could be an alias.
                locale = locales.Locale.from_alias(self, locale)
        if locale is not None:
            locale.set_alias(self)
        return locale

    def normalize_locales(self, locale_list):
        for locale in locale_list:
            locale.set_alias(self)
        return locale_list

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
                    contents = self.untag(fields, locale=locale)
                    self.podcache.file_cache.add(path, contents, locale=locale)
                except Exception:
                    logging.error('Error parsing -> {}'.format(path))
                    raise
        return contents

    def reset_yaml(self):
        # Mark that the yaml needs to be reparsed.
        self._yaml = utils.SENTINEL
        # Tell the cached property to reset.
        # pylint: disable=no-member
        self._parse_yaml.reset()

    def untag(self, contents, locale=None):
        """Untag data using the pod specific untagging params."""
        return untag.Untag.untag(
            contents, locale_identifier=locale, params={
                'env': untag.UntagParamRegex(self.env.name),
            })

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
