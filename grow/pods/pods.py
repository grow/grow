"""A pod encapsulates all files used to build a site."""

from . import catalog_holder
from . import collection
from . import document_fields
from . import env as environment
from . import locales
from . import messages
from . import podcache
from . import podspec
from . import routes
from . import static
from . import storage
from . import tags
from ..preprocessors import preprocessors
from ..translators import translators
from grow.common import sdk_utils
from grow.common import utils
from werkzeug.contrib import cache as werkzeug_cache
import copy
import jinja2
import json
import logging
import os
import progressbar
import re
import time
import yaml

_handler = logging.StreamHandler()
_formatter = logging.Formatter('[%(asctime)s] %(message)s', '%H:%M:%S')
_handler.setFormatter(_formatter)
_logger = logging.getLogger('pod')
_logger.propagate = False
_logger.addHandler(_handler)


class Error(Exception):
    pass


class PodDoesNotExistError(Error, IOError):
    pass


# TODO(jeremydw): A handful of the properties of "pod" should be moved to the
# "podspec" class.

class Pod(object):

    FEATURE_UI = 'ui'
    FILE_PODCACHE = '.podcache.yaml'
    FILE_PODSPEC = 'podspec.yaml'

    def __eq__(self, other):
        return (isinstance(self, Pod)
                and isinstance(other, Pod)
                and self.root == other.root)

    def __init__(self, root, storage=storage.auto, env=None):
        self.storage = storage
        self.root = (root if self.storage.is_cloud_storage
                     else os.path.abspath(root))
        self.env = (env if env
                    else environment.Env(environment.EnvConfig(host='localhost')))
        self.locales = locales.Locales(pod=self)
        self.catalogs = catalog_holder.Catalogs(pod=self)
        self.logger = _logger
        self.routes = routes.Routes(pod=self)
        self._podcache = None
        self._disabled = set()

        # Ensure preprocessors are loaded when pod is initialized.
        # Preprocessors may modify the environment in ways that are required by
        # data files (e.g. yaml constructors).
        if self.exists:
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

    def _parse_cache_yaml(self):
        podcache_file_name = '/{}'.format(self.FILE_PODCACHE)
        if not self.file_exists(podcache_file_name):
            return
        try:
            # Do not use the utils.parse_yaml as that has extra constructors
            # that should not be run when the cache file is being parsed.
            return yaml.load(self.read_file(podcache_file_name)) or {}
        except IOError as e:
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
    def flags(self):
        return self.yaml.get('flags', {})

    @property
    def grow_version(self):
        return self.podspec.grow_version

    @property
    def podcache(self):
        if not self._podcache:
            self._podcache = podcache.PodCache(
                yaml=self._parse_cache_yaml() or {}, pod=self)
        return self._podcache

    @property
    def podspec(self):
        return podspec.PodSpec(yaml=self.yaml, pod=self)

    @property
    def title(self):
        return self.yaml.get('title')

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
        return self._parse_yaml() or {}

    def abs_path(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return os.path.join(self.root, path)

    def create_collection(self, collection_path, fields):
        pod_path = os.path.join(collection.Collection.CONTENT_PATH, collection_path)
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

    def disable(self, feature):
        self._disabled.add(feature)

    def dump(self, suffix='index.html', append_slashes=True):
        output = self.export(suffix=suffix, append_slashes=append_slashes)
        if self.ui and not self.is_enabled(self.FEATURE_UI):
            output.update(self.export_ui())
        return output

    def export(self, suffix=None, append_slashes=False):
        """Builds the pod, returning a mapping of paths to content."""
        output = {}
        routes = self.get_routes()
        paths = []
        for items in routes.get_locales_to_paths().values():
            paths += items
        text = 'Building: %(value)d/{} (in %(elapsed)s)'
        widgets = [progressbar.FormatLabel(text.format(len(paths)))]
        bar = progressbar.ProgressBar(widgets=widgets, maxval=len(paths))
        bar.start()
        for path in paths:
            output_path = path
            controller, params = self.match(path)
            # Append a suffix onto rendered routes only. This supports dumping
            # paths that would serve at URLs that terminate in "/" or without
            # an extension to an HTML file suitable for writing to a
            # filesystem. Static routes and other routes that may export to
            # paths without extensions should remain unmodified.
            if suffix and controller.KIND == messages.Kind.RENDERED:
                if (append_slashes
                    and not output_path.endswith('/')
                    and not os.path.splitext(output_path)[-1]):
                    output_path = output_path.rstrip('/') + '/'
                if append_slashes and output_path.endswith('/') and suffix:
                    output_path += suffix
            try:
                output[output_path] = controller.render(params, inject=False)
            except:
              self.logger.error('Error building: {}'.format(controller))
              raise
            bar.update(bar.currval + 1)
        error_controller = routes.match_error('/404.html')
        if error_controller:
            output['/404.html'] = error_controller.render({})
        bar.finish()
        return output

    def export_ui(self):
        """Builds the grow ui tools, returning a mapping of paths to content."""
        output = {}
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
            output[output_path] = self.storage.read(source_path)

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

        text = 'Building UI Tools: %(value)d/{} (in %(elapsed)s)'
        widgets = [progressbar.FormatLabel(text.format(len(paths)))]
        bar = progressbar.ProgressBar(widgets=widgets, maxval=len(paths))
        bar.start()
        for path in paths:
            output_path = path.replace(
                source_prefix, '{}{}'.format(destination_root, tools_dir))
            output[output_path] = self.read_file(path)
            bar.update(bar.currval + 1)
        bar.finish()
        return output

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
        pod_path = os.path.join(collection.Collection.CONTENT_PATH, collection_path)
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
            deployment = deployments.make_deployment(kind, config, name=nickname)
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
        env = jinja2.Environment(**kwargs)
        env.filters.update(tags.create_builtin_filters())
        get_gettext_func = self.catalogs.get_gettext_translations
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
                    return static.StaticFile(pod_path, serving_path, locale=locale,
                                             pod=self, controller=controller,
                                             fingerprinted=controller.fingerprinted,
                                             localization=controller.localization)
        text = ('Either no file exists at "{}" or the "static_dirs" setting was '
                'not configured for this path in {}.'.format(
                    pod_path, self.FILE_PODSPEC))
        raise static.BadStaticFileError(text)

    def get_podspec(self):
        return self.podspec

    def get_root_path(self, locale=None):
        path_format = self.yaml.get('flags', {}).get('root_path', None)
        if locale is None:
            locale = self.yaml.get('localization', {}).get('default_locale', '')
        if not path_format:
            return '/'
        return path_format.format(**{'locale': locale})

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
            valid_service_kinds = [each['service'] for each in translator_services]
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
        extensions = []
        for name in self.yaml.get('extensions', {}).get('jinja2', []):
            try:
                value = utils.import_string(name, [self.root])
            except ImportError:
                logging.error(
                    'Error importing %s. Module path must be relative to '
                    'the pod root.', repr(name))
                raise
            extensions.append(value)
        return extensions

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
            self.routes.reset_cache(rebuild=True)

        if pod_path.startswith(collection.Collection.CONTENT_PATH):
            col = self.get_doc(pod_path).collection
            base_docs = []
            original_docs = []
            updated_docs = []

            for dep_path in self.podcache.dependency_graph.get_dependents(
                    pod_path):
                base_docs.append(self.get_doc(dep_path))
                original_docs += col.list_servable_document_locales(dep_path)

            for doc in base_docs:
                self.podcache.document_cache.remove(doc)
                self.podcache.collection_cache.remove_document_locales(doc)

            # The routing map should remain unchanged unless the file change
            # caused the serving path of a doc to change.
            changed_docs = []
            for i, original_doc in enumerate(original_docs):
                updated_doc = self.get_doc(
                    original_doc.pod_path, original_doc._locale_kwarg)
                if (updated_doc.has_serving_path()
                        and original_doc.get_serving_path() != updated_doc.get_serving_path()):
                    changed_docs.append((original_doc, updated_doc))
            if changed_docs:
                self.routes.reconcile_documents(
                    remove_docs=[x[0] for x in changed_docs],
                    add_docs=[x[1] for x in changed_docs])

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

    def read_yaml(self, path):
        fields = utils.parse_yaml(self.read_file(path), pod=self)
        return document_fields.DocumentFields._untag(fields)

    def reset_yaml(self):
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
