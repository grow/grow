"""A pod encapsulates all files used to build a site."""

import copy
import json
import logging
import os
import sys
import time
import progressbar
import yaml
import jinja2
from werkzeug.contrib import cache as werkzeug_cache
from grow.common import extensions
from grow.common import logger
from grow.common import sdk_utils
from grow.common import progressbar_non
from grow.common import utils
from grow.performance import profile
from grow.preprocessors import preprocessors
from grow.templates import filters
from grow.templates import jinja_dependency
from grow.translators import translation_stats
from grow.translators import translators
# NOTE: exc imported directly, webob.exc doesn't work when frozen.
from webob import exc as webob_exc
from . import catalog_holder
from . import collection
from . import document_fields
from . import env as environment
from . import locales
from . import messages
from . import podcache
from . import podspec
from . import routes as grow_routes
from . import static as grow_static
from . import storage as grow_storage


class Error(Exception):
    pass


class PodDoesNotExistError(Error, IOError):
    pass


# TODO(jeremydw): A handful of the properties of "pod" should be moved to the
# "podspec" class.

class Pod(object):
    DEFAULT_EXTENSIONS_DIR_NAME = 'extensions'
    FEATURE_UI = 'ui'
    FEATURE_TRANSLATION_STATS = 'translation_stats'
    FILE_PODCACHE = '.podcache.yaml'
    FILE_PODSPEC = 'podspec.yaml'
    PATH_CONTROL = '/.grow/'

    def __eq__(self, other):
        return (isinstance(self, Pod)
                and isinstance(other, Pod)
                and self.root == other.root)

    def __init__(self, root, storage=grow_storage.auto, env=None, load_extensions=True):
        self._yaml = utils.SENTINEL
        self.storage = storage
        self.root = (root if self.storage.is_cloud_storage
                     else os.path.abspath(root))
        self.env = (env if env
                    else environment.Env(environment.EnvConfig(host='localhost')))
        self.locales = locales.Locales(pod=self)
        self.catalogs = catalog_holder.Catalogs(pod=self)
        self.routes = grow_routes.Routes(pod=self)
        self._podcache = None
        self._disabled = set(
            self.FEATURE_TRANSLATION_STATS,
        )

        # Ensure preprocessors are loaded when pod is initialized.
        # Preprocessors may modify the environment in ways that are required by
        # data files (e.g. yaml constructors). Avoid loading extensions using
        # `load_extensions=False` to permit `grow install` to be used to
        # actually install extensions, prior to loading them.
        if load_extensions and self.exists:
            # Modify sys.path for built-in extension support.
            _ext_dir = self.abs_path(self.extensions_dir)
            if os.path.exists(_ext_dir):
                sys.path.insert(0, _ext_dir)
            self.list_preprocessors()
        try:
            sdk_utils.check_sdk_version(self)
        except PodDoesNotExistError:
            pass  # Pod doesn't exist yet, simply pass.

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '<Pod: {}>'.format(self.root)

    @utils.memoize
    def _get_bytecode_cache(self):
        return jinja2.MemcachedBytecodeCache(client=self.cache)

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

    def _parse_cache_yaml(self):
        podcache_file_name = '/{}'.format(self.FILE_PODCACHE)
        if not self.file_exists(podcache_file_name):
            return
        try:
            # Do not use the utils.parse_yaml as that has extra constructors
            # that should not be run when the cache file is being parsed.
            return yaml.load(self.read_file(podcache_file_name)) or {}
        except IOError:
            path = self.abs_path(podcache_file_name)
            raise podcache.PodCacheParseError('Error parsing: {}'.format(path))

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
        if env and env.name:
            untag = document_fields.DocumentFields.untag
            content = untag(self._parse_yaml(), env_name=env.name)
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
    def grow_version(self):
        return self.podspec.grow_version

    @property
    def logger(self):
        return logger.LOGGER

    @property
    def podcache(self):
        if not self._podcache:
            self._podcache = podcache.PodCache(
                yaml=self._parse_cache_yaml() or {}, pod=self)
        return self._podcache

    @property
    def podspec(self):
        return podspec.PodSpec(yaml=self.yaml, pod=self)

    @utils.cached_property
    def profile(self):
        """Profile object for code timing."""
        return profile.Profile()

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
        self._disabled.add(feature)

    def dump(self, suffix='index.html', append_slashes=True, pod_paths=None):
        for output_path, rendered in self.export(
                suffix=suffix, append_slashes=append_slashes, pod_paths=pod_paths):
            yield output_path, rendered
        if self.ui and not self.is_enabled(self.FEATURE_UI):
            for output_path, rendered in self.export_ui():
                yield output_path, rendered

    def enable(self, feature):
        self._disabled.discard(feature)

    def export(self, suffix=None, append_slashes=False, pod_paths=None):
        """Builds the pod, returning a mapping of paths to content based on pod routes."""
        paths, routes = self.determine_paths_to_build(pod_paths=pod_paths)
        for output_path, rendered in self.render_paths(
                paths, routes, suffix=suffix, append_slashes=append_slashes):
            yield output_path, rendered
        if not pod_paths:
            error_controller = routes.match_error('/404.html')
            if error_controller:
                yield '/404.html', error_controller.render({})

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
            yield output_path, self.storage.read(source_path)

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
            yield output_path, self.read_file(path)
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
        get_gettext_func = self.catalogs.get_gettext_translations
        # pylint: disable=no-member
        env.install_gettext_callables(
            lambda x: get_gettext_func(locale).ugettext(x),
            lambda s, p, n: get_gettext_func(locale).ungettext(s, p, n),
            newstyle=True)
        return env

    def get_routes(self):
        return self.routes

    def get_static(self, pod_path, locale=None):
        """Returns a StaticFile, given the static file's pod path."""
        for route in self.routes.static_routing_map.iter_rules():
            controller = route.endpoint
            if controller.KIND == messages.Kind.STATIC:
                serving_path = controller.match_pod_path(pod_path)
                if serving_path:
                    return grow_static.StaticFile(pod_path, serving_path, locale=locale,
                                                  pod=self, controller=controller,
                                                  fingerprinted=controller.fingerprinted,
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
        return feature not in self._disabled

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
            preprocessor = preprocessors.make_preprocessor(kind, params, self)
            results.append(preprocessor)
        return results

    def list_statics(self, pod_path, locale=None, include_hidden=False):
        for path in self.list_dir(pod_path):
            if include_hidden or not path.rsplit(os.sep, 1)[-1].startswith('.'):
                yield self.get_static(pod_path + path, locale=locale)

    def load(self):
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
            locale = locales.Locale.parse(locale)
        if locale is not None:
            locale.set_alias(self)
        return locale

    def on_file_changed(self, pod_path):
        """Handle when a single file has changed in the pod."""
        if pod_path == '/{}'.format(self.FILE_PODSPEC):
            self.reset_yaml()
            self.podcache.reset()
            self.routes.reset_cache(rebuild=True)
        elif (pod_path.endswith(collection.Collection.BLUEPRINT_PATH)
                and pod_path.startswith(collection.Collection.CONTENT_PATH)):
            doc = self.get_doc(pod_path)
            self.podcache.collection_cache.remove_collection(doc.collection)
            self.routes.reset_cache(rebuild=True)
        elif pod_path.startswith(collection.Collection.CONTENT_PATH):
            trigger_doc = self.get_doc(pod_path)
            col = trigger_doc.collection
            base_docs = []
            original_docs = []
            trigger_docs = col.list_servable_document_locales(pod_path)
            updated_docs = []

            for dep_path in self.podcache.dependency_graph.get_dependents(
                    pod_path):
                base_docs.append(self.get_doc(dep_path))
                original_docs += col.list_servable_document_locales(dep_path)

            for doc in base_docs:
                self.podcache.document_cache.remove(doc)
                self.podcache.collection_cache.remove_document_locales(doc)

            # The routing map should remain unchanged most of the time.
            added_docs = []
            removed_docs = []
            for original_doc in original_docs:
                # Removed documents should be removed.
                if not original_doc.exists:
                    removed_docs.append(original_doc)
                    continue

                updated_doc = self.get_doc(
                    original_doc.pod_path, original_doc._locale_kwarg)

                # When the serving path has changed, updated in routes.
                if (updated_doc.has_serving_path()
                        and original_doc.get_serving_path() != updated_doc.get_serving_path()):
                    added_docs.append(updated_doc)
                    removed_docs.append(original_doc)

                # If the locales change then we need to adjust the routes.
                original_locales = set([str(l) for l in original_doc.locales])
                updated_locales = set([str(l) for l in updated_doc.locales])

                new_locales = updated_locales - original_locales
                for locale in new_locales:
                    new_doc = self.get_doc(original_doc.pod_path, locale)
                    if new_doc.has_serving_path() and new_doc not in added_docs:
                        added_docs.append(new_doc)

                removed_locales = original_locales - updated_locales
                for locale in removed_locales:
                    removed_doc = self.get_doc(original_doc.pod_path, locale)
                    if removed_doc.has_serving_path():
                        if removed_doc not in removed_docs:
                            removed_docs.append(removed_doc)

            # Check for new docs.
            route_env = self.env.to_wsgi_env()
            for trigger_doc in trigger_docs:
                if trigger_doc.has_serving_path():
                    try:
                        _ = self.routes.match(trigger_doc.get_serving_path(), env=route_env)
                    except webob_exc.HTTPNotFound:
                        added_docs.append(trigger_doc)
            if added_docs or removed_docs:
                self.routes.reconcile_documents(
                    remove_docs=removed_docs, add_docs=added_docs)

    def open_file(self, pod_path, mode=None):
        path = self._normalize_path(pod_path)
        return self.storage.open(path, mode=mode)

    def preprocess(self, preprocessor_names=None, run_all=False, tags=None,
                   build=True, ratelimit=None):
        if not preprocessor_names:
            self.catalogs.compile()  # Preprocess translations.
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
        return utils.get_rows_from_csv(pod=self, path=path, locale=locale)

    def read_file(self, pod_path):
        path = self._normalize_path(pod_path)
        return self.storage.read(path)

    def read_json(self, path):
        fp = self.open_file(path)
        return json.load(fp)

    def read_yaml(self, path, locale=None):
        fields = utils.parse_yaml(self.read_file(path), pod=self)
        try:
            untag = document_fields.DocumentFields.untag
            return untag(fields, env_name=self.env.name, locale=locale)
        except Exception as e:
            logging.error('Error parsing -> {}'.format(path))
            raise

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
                key = 'pod.render_paths.render'
                if isinstance(controller, grow_static.StaticController):
                    key = 'pod.render_paths.render.static'

                with self.profile.timer(key, label=output_path, meta={'path': output_path}):
                    yield (output_path, controller.render(params, inject=False))
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
        path = self._normalize_path(pod_path)
        self.storage.write(path, content)

    def write_yaml(self, path, content):
        self.podcache.collection_cache.remove_by_path(path)
        self.podcache.document_cache.remove_by_path(path)
        content = utils.dump_yaml(content)
        self.write_file(path, content)
