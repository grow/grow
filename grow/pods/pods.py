"""A pod encapsulates all files used to build a web site.

Pods are the main interface to everything in a web site. Specifically, pods are
used to do the following sorts of tasks:

  - manage content (collections, blueprints, and documents)
  - manage pod files (any of the files contained in the pod)
  - list routes
  - building and deployment
  - listing and running tests

Pods are accessed using their root directory.

  pod = pods.Pod('/home/growler/my-site/')

You can get a content collection from the pod.

  collection = pod.get_collection('/content/pages/')

You can get a content document from the pod.

  document = pod.get_doc('/content/pages/index.md')

You can get a static file from the pod.

  file = pod.get_file('/podspec.yaml')
"""

from . import env as environment
from . import files
from . import locales
from . import messages
from . import podspec
from . import routes
from . import storage
from .catalogs import catalog_holder
from .controllers import jinja2htmlcompress
from .controllers import messages as controller_messages
from .controllers import static
from .controllers import tags
from .documents import collection
from .preprocessors import preprocessors
from .tests import tests
from babel import dates as babel_dates
from grow.common import sdk_utils
from grow.common import utils
from grow.deployments import deployments
from werkzeug.contrib import cache as werkzeug_cache
import copy
import jinja2
import logging
import os
import progressbar
import re

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


class PodSpecParseError(Error):
    pass


# TODO(jeremydw): A handful of the properties of "pod" should be moved to the
# "podspec" class.

class Pod(object):

    def __init__(self, root, storage=storage.auto, env=None):
        self.storage = storage
        self.root = (root if self.storage.is_cloud_storage
                     else os.path.abspath(root))
        self.env = (env if env
                    else environment.Env(environment.EnvConfig(host='localhost')))
        self.locales = locales.Locales(pod=self)
        self.tests = tests.Tests(pod=self)
        self.catalogs = catalog_holder.Catalogs(pod=self)
        self.logger = _logger
        self._routes = None
        self._template_env = None
        try:
            sdk_utils.check_sdk_version(self)
        except PodDoesNotExistError:
            pass  # Pod doesn't exist yet, simply pass.

    def __repr__(self):
        return '<Pod: {}>'.format(self.root)

    def __eq__(self, other):
        return (isinstance(self, Pod)
                and isinstance(other, Pod)
                and self.root == other.root)

    def __ne__(self, other):
        return not self.__eq__(other)

    def exists(self):
        return self.file_exists('/podspec.yaml')

    @property
    def yaml(self):
        return self._parse_yaml()

    @property
    def routes(self):
        if self._routes is None:
            self._routes = routes.Routes(pod=self)
        return self._routes

    def reset_yaml(self):
        self._parse_yaml.reset()

    @property
    def grow_version(self):
        return self.podspec.grow_version

    @utils.memoize
    def _parse_yaml(self):
        try:
            return utils.parse_yaml(self.read_file('/podspec.yaml'))
        except IOError as e:
            path = self.abs_path('/podspec.yaml')
            if e.args[0] == 2 and e.filename:
                raise PodDoesNotExistError('Pod does not exist: {}'.format(path))
            raise PodSpecParseError('Error parsing: {}'.format(path))

    @property
    def podspec(self):
        return podspec.Podspec(yaml=self.yaml, pod=self)

    @property
    def error_routes(self):
        return self.yaml.get('error_routes')

    @property
    def flags(self):
        return self.yaml.get('flags', {})

    @property
    def title(self):
        return self.yaml.get('title')

    def match(self, path):
        return self.routes.match(path, env=self.env.to_wsgi_env())

    def get_routes(self):
        return self.routes

    def abs_path(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return os.path.join(self.root, path)

    def list_dir(self, pod_path='/'):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return self.storage.listdir(path)

    def open_file(self, pod_path, mode=None):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return self.storage.open(path, mode=mode)

    def file_modified(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return self.storage.modified(path)

    def read_file(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return self.storage.read(path)

    def write_file(self, pod_path, content):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        self.storage.write(path, content)

    def file_size(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return self.storage.size(path)

    def file_exists(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return self.storage.exists(path)

    def delete_file(self, pod_path):
        path = os.path.join(self.root, pod_path.lstrip('/'))
        return self.storage.delete(path)

    def move_file_to(self, source_pod_path, destination_pod_path):
        source_path = os.path.join(self.root, source_pod_path.lstrip('/'))
        dest_path = os.path.join(self.root, destination_pod_path.lstrip('/'))
        return self.storage.move_to(source_path, dest_path)

    def list_collections(self, paths=None):
        cols = collection.Collection.list(self)
        if paths:
            return [col for col in cols if col.collection_path in paths]
        return cols

    def get_file(self, pod_path):
        return files.File.get(pod_path, self)

    def create_file(self, pod_path, content):
        """Creates a file inside the pod."""
        return files.File.create(pod_path, content, self)

    def list_statics(self, pod_path, locale=None):
        for path in self.list_dir(pod_path):
            yield self.get_static(pod_path + path, locale=locale)

    def get_static(self, pod_path, locale=None):
        """Returns a StaticFile, given the static file's pod path."""
        for route in self.routes:
            controller = route.endpoint
            if controller.KIND == controller_messages.Kind.STATIC:
                serving_path = controller.match_pod_path(pod_path)
                if serving_path:
                    return static.StaticFile(pod_path, serving_path, locale=locale,
                                             pod=self, controller=controller,
                                             fingerprinted=controller.fingerprinted,
                                             localization=controller.localization)
        text = ('Either no file exists at "{}" or the "static_dirs" setting was '
                'not configured for this path in podspec.yaml.'.format(pod_path))
        raise static.BadStaticFileError(text)

    def get_doc(self, pod_path, locale=None):
        """Returns a document, given the document's pod path."""
        collection_path, unused_path = os.path.split(pod_path)
        if not collection_path or not unused_path:
            text = '"{}" is not a path to a document.'.format(pod_path)
            raise collection.BadCollectionNameError(text)
        collection = self.get_collection(collection_path)
        return collection.get_doc(pod_path, locale=locale)

    def get_home_doc(self):
        home = self.yaml.get('home')
        if home is None:
            return None
        return self.get_doc(home)

    def get_catalogs(self, template_path=None):
        return catalog_holder.Catalogs(pod=self, template_path=template_path)

    def get_collection(self, collection_path):
        """Returns a collection.

        Args:
          collection_path: A collection's path relative to the /content/ directory.
        Returns:
          Collection.
        """
        pod_path = os.path.join('/content', collection_path)
        return collection.Collection.get(pod_path, _pod=self)

    def duplicate_to(self, other, exclude=None):
        """Duplicates this pod to another pod."""
        if not isinstance(other, self.__class__):
            raise ValueError('{} is not a pod.'.format(other))
        source_paths = self.list_dir('/')
        for path in source_paths:
            if exclude:
                patterns = '|'.join(['({})'.format(pattern) for pattern in exclude])
                if re.match(patterns, path) or 'theme/' in path:
                    continue
            content = self.read_file(path)
            other.write_file(path, content)
        # TODO: Handle same-storage copying more elegantly.

    def export(self):
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
            controller = self.match(path)
            output[path] = controller.render()
            bar.update(bar.currval + 1)
        error_controller = routes.match_error('/404.html')
        if error_controller:
            output['/404.html'] = error_controller.render()
        bar.finish()
        return output

    def dump(self, suffix='index.html', append_slashes=True):
        output = self.export()
        clean_output = {}
        if suffix:
            for path, content in output.iteritems():
                if (append_slashes
                    and not path.endswith('/')
                    and not os.path.splitext(path)[-1]):
                    path = path.rstrip('/') + '/'
                if append_slashes and path.endswith('/') and suffix:
                    path += suffix
                clean_output[path] = content
        else:
            clean_output = output
        return clean_output

    def to_message(self):
        message = messages.PodMessage()
        message.collections = [collection.to_message()
                               for collection in self.list_collections()]
        message.routes = self.routes.to_message()
        return message

    def delete(self):
        """Deletes the pod by deleting all of its files."""
        pod_paths = self.list_dir('/')
        for path in pod_paths:
            self.delete_file(path)
        return pod_paths

    def list_deployments(self):
        destination_configs = self.yaml['deployments']
        results = []
        for name in destination_configs.keys():
            results.append(self.get_deployment(name))
        return results

    def get_deployment(self, nickname):
        """Returns a pod-specific deployment."""
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
        if deployment.config.keep_control_dir:
            deployment.pod = self
        return deployment

    def list_locales(self):
        codes = self.yaml.get('localization', {}).get('locales', [])
        return locales.Locale.parse_codes(codes)

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

    def preprocess(self, preprocessor_names=None, run_all=False):
        self.catalogs.compile(force=run_all)  # Preprocess translations.
        for preprocessor in self.list_preprocessors():
            if preprocessor_names:
                if preprocessor.name in preprocessor_names:
                    preprocessor.run()
            elif preprocessor.autorun or run_all:
                preprocessor.run()

    def get_podspec(self):
        return self.podspec

    @utils.memoize
    def _get_bytecode_cache(self):
        # NOTE: It is safe to reuse the same bytecode cache across locales.
        client = werkzeug_cache.SimpleCache()
        return jinja2.MemcachedBytecodeCache(client=client)

    def list_jinja_extensions(self):
        extensions = []
        for name in self.yaml.get('extensions', {}).get('jinja2', []):
            try:
                value = utils.import_string(name, [self.root])
            except:
                raise PodSpecParseError(
                    'Could not import {}: must use dot syntax relative to the pod root'
                    .format(repr(name))
                )
            extensions.append(value)
        return extensions

    @utils.memoize
    def create_template_env(self, locale=None, root=None):
        # NOTE: The template environment cannot be reused across locales, since
        # gettext translations can/should not be unintalled across locales. If the
        # environment is reused across locales, translation leakage can occur.
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
        if self.podspec.flags.get('compress_html'):
            kwargs['extensions'].append(jinja2htmlcompress.HTMLCompress)
        kwargs['extensions'].extend(self.list_jinja_extensions())
        env = jinja2.Environment(**kwargs)
        filters = (
            ('date', babel_dates.format_date),
            ('datetime', babel_dates.format_datetime),
            ('deeptrans', tags.deeptrans),
            ('jsonify', tags.jsonify),
            ('markdown', tags.markdown_filter),
            ('render', tags.render_filter),
            ('slug', tags.slug_filter),
            ('time', babel_dates.format_time),
        )
        env.filters.update(filters)
        env.active_locale = '__unset'
        return env

    def get_root_path(self, locale=None):
        path_format = self.yaml.get('flags', {}).get('root_path', None)
        if locale is None:
            locale = self.yaml.get('localization', {}).get('default_locale', '')
        if not path_format:
            return '/'
        return path_format.format(**{'locale': locale})

    def test(self):
        self.tests.run()

    def normalize_locale(self, locale, default=None):
        locale = locale or default or self.podspec.default_locale
        if isinstance(locale, basestring):
            locale = locales.Locale.parse(locale)
        if locale is not None:
            locale.set_alias(self)
        return locale

    def load(self):
        self.routes.routing_map
