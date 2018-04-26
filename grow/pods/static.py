from . import controllers
from . import messages
from grow.common import urls
from grow.translations import locales
from datetime import datetime
import fnmatch
import hashlib
import mimetypes
import os
import re
import time
import webob
import yaml

mimetypes.add_type('application/font-woff', '.woff')
mimetypes.add_type('application/font-woff', '.woff')
mimetypes.add_type('image/bmp', '.cur')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('text/css', '.css')


SKIP_PATTERNS = [
    '**/.**',
]


class Error(Exception):
    pass


class BadStaticFileError(Error):
    pass


class StaticFile(object):

    def __init__(self, pod_path, serving_path, locale=None, localization=None,
                 controller=None, fingerprinted=False, pod=None):
        self.pod = pod
        self.default_locale = pod.podspec.default_locale
        self.locale = pod.normalize_locale(locale)
        self.localization = localization
        self.pod_path = pod_path
        self.serving_path = serving_path
        self.controller = controller
        self.basename = os.path.basename(pod_path)
        self.fingerprinted = fingerprinted
        self.base, self.ext = os.path.splitext(self.basename)

    def __repr__(self):
        if self.locale:
            return "<StaticFile({}, locale='{}')>".format(self.pod_path, self.locale)
        return "<StaticFile({})>".format(self.pod_path)

    def __eq__(self, other):
        return (self.pod_path == other.pod_path and self.pod == other.pod
                and other.locale == self.locale)

    def __ne__(self, other):
        return not self.__eq__(other)

    @property
    def exists(self):
        return self.pod.file_exists(self.pod_path)

    @property
    def modified(self):
        return self.pod.file_modified(self.pod_path)

    @property
    def size(self):
        return self.pod.file_size(self.pod_path)

    @property
    def fingerprint(self):
        return StaticFile._create_fingerprint(self.pod, self.pod_path)

    @staticmethod
    def _create_fingerprint(pod, pod_path):
        md5 = hashlib.md5()
        with pod.open_file(pod_path, 'rb') as fp:
            content = fp.read()
            md5.update(content)
        return md5.hexdigest()

    @staticmethod
    def remove_fingerprint(path):
        base, _ = os.path.splitext(path)
        if base.endswith('.min'):
            return re.sub('(.*)-([a-fA-F\d]{32})\.min\.(.*)', r'\g<1>.min.\g<3>', path)
        return re.sub('(.*)-([a-fA-F\d]{32})\.(.*)', r'\g<1>.\g<3>', path)

    @staticmethod
    def apply_fingerprint(path, fingerprint):
        base, ext = os.path.splitext(path)
        # Special case to preserve ".min.<ext>" extension lockup.
        if base.endswith('.min'):
            base = base[:-4]
            return '{}-{}.min{}'.format(base, fingerprint, ext)
        else:
            return '{}-{}{}'.format(base, fingerprint, ext)

    @property
    def url(self):
        serving_path = self.serving_path
        path_format = self.controller.path_format.replace('{filename}', '')
        if '{fingerprint}' in path_format:
            path_format = path_format.replace('{fingerprint}', self.fingerprint)
        # Determine suffix only after all replacements are made.
        suffix = serving_path.replace(path_format, '')
        if self.localization:
            if self.fingerprinted:
                suffix = StaticFile.remove_fingerprint(suffix)
            localized_pod_path = self.localization['static_dir'] + suffix
            localized_pod_path = localized_pod_path.format(locale=self.locale)
            localized_pod_path = localized_pod_path.replace('//', '/')
            if self.pod.file_exists(localized_pod_path):
                # TODO(jeremydw): Centralize path formatting.
                # Internal paths use Babel locales, serving paths use aliases.
                locale = self.locale.alias if self.locale is not None else self.locale
                localized_serving_path = self.localization['serve_at'] + suffix
                kwargs = {
                    'locale': locale,
                    'root': self.pod.podspec.root,
                }
                if '{fingerprint}' in localized_serving_path:
                    fingerprint = StaticFile._create_fingerprint(
                        self.pod, localized_pod_path)
                    kwargs['fingerprint'] = fingerprint
                localized_serving_path = localized_serving_path.format(**kwargs)
                if self.fingerprinted and localized_serving_path:
                    fingerprint = StaticFile._create_fingerprint(self.pod, localized_pod_path)
                    localized_serving_path = StaticFile.apply_fingerprint(localized_serving_path, fingerprint)
                serving_path = localized_serving_path.replace('//', '/')
        if serving_path:
            return urls.Url(
                path=serving_path,
                host=self.pod.env.host,
                port=self.pod.env.port,
                scheme=self.pod.env.scheme)


class StaticController(controllers.BaseController):
    KIND = messages.Kind.STATIC

    def __init__(self, path_format, source_format=None, localized=False,
                 localization=None, fingerprinted=False, pod=None):
        # path_format: "serve_at"
        # source_format: "static_dir"
        self.path_format = path_format.replace('<grow:', '{').replace('>', '}')
        self.source_format = source_format.replace('<grow:', '{').replace('>', '}')
        self.pod = pod
        self.localized = localized
        self.localization = localization
        self.fingerprinted = fingerprinted

    def __repr__(self):
        return '<Static(format=\'{}\')>'.format(self.source_format)

    def get_localized_pod_path(self, params):
        if (self.localization
           and '{locale}' in self.localization['static_dir']
           and 'locale' in params):
            source_format = self.localization['serve_at']
            source_format += '/{filename}'
            source_format = source_format.replace('//', '/')
            kwargs = params
            kwargs['root'] = self.pod.podspec.root
            if 'locale' in kwargs:
                locale = locales.Locale.from_alias(self.pod, kwargs['locale'])
                kwargs['locale'] = str(locale)
            if '{root}' in source_format:
                kwargs['root'] = self.pod.podspec.root
            pod_path = source_format.format(**kwargs)
            if self.fingerprinted:
                pod_path = StaticFile.remove_fingerprint(pod_path)
            if self.pod.file_exists(pod_path):
                return pod_path

    def get_pod_path(self, params):
        # If a localized file exists, serve it. Otherwise, serve the base file.
        pod_path = self.get_localized_pod_path(params)
        if pod_path:
            return pod_path
        pod_path = self.source_format.format(**params)
        if self.fingerprinted:
            pod_path = StaticFile.remove_fingerprint(pod_path)
        return pod_path

    def validate(self, params):
        pod_path = self.get_pod_path(params)
        if not self.pod.file_exists(pod_path):
            path = self.pod.abs_path(pod_path)
            message = '{} does not exist.'.format(path)
            raise webob.exc.HTTPNotFound(message)

    def render(self, params, inject=False):
        pod_path = self.get_pod_path(params)
        return self.pod.read_file(pod_path)

    def get_mimetype(self, params):
        pod_path = self.get_pod_path(params)
        return mimetypes.guess_type(pod_path)[0]

    def get_http_headers(self, params):
        pod_path = self.get_pod_path(params)
        path = self.pod.abs_path(pod_path)
        headers = super(StaticController, self).get_http_headers(params)
        self.pod.storage.update_headers(headers, path)
        modified = self.pod.storage.modified(path)
        time_obj = datetime.fromtimestamp(modified).timetuple()
        time_format = '%a, %d %b %Y %H:%M:%S GMT'
        headers['Last-Modified'] =  time.strftime(time_format, time_obj)
        headers['ETag'] = '"{}"'.format(headers['Last-Modified'])
        headers['X-Grow-Pod-Path'] = pod_path
        if self.locale:
            headers['X-Grow-Locale'] = self.locale
        return headers

    def match_pod_path(self, pod_path):
        if self.path_format == pod_path:
            if self.fingerprinted:
                fingerprint = StaticFile._create_fingerprint(self.pod, pod_path)
                return StaticFile.apply_fingerprint(self.path_format, fingerprint)
            return self.path_format
        tokens = re.findall('.?{([^}]+)}.?', self.path_format)
        if 'filename' in tokens:
            source_regex = self.source_format.replace(
                '{filename}', '(?P<filename>.*)')
            source_regex = source_regex.replace('{locale}', '(?P<locale>[^/]*)')
            source_regex = source_regex.replace('{fingerprint}', '(?P<fingerprint>[^/])')
            source_regex = source_regex.replace('{root}', '(?P<root>[^/])')
            match = re.match(source_regex, pod_path)
            if match:
                kwargs = match.groupdict()
                kwargs['root'] = self.pod.podspec.root
                if 'fingerprint' in tokens:
                    fingerprint = StaticFile._create_fingerprint(self.pod, pod_path)
                    kwargs['fingerprint'] = fingerprint
                if 'locale' in kwargs:
                    locale = locales.Locale.from_alias(self.pod, kwargs['locale'])
                    kwargs['locale'] = str(locale)
                path = self.path_format.format(**kwargs)
                path = path.replace('//', '/')
                if self.fingerprinted:
                    fingerprint = StaticFile._create_fingerprint(self.pod, pod_path)
                    path = StaticFile.apply_fingerprint(path, fingerprint)
                return path

    def list_concrete_paths(self):
        concrete_paths = set()
        tokens = re.findall('.?{([^}]+)}.?', self.path_format)

        source_regex = self.source_format.replace('{filename}', '(?P<filename>.*)')
        source_regex = source_regex.replace('{locale}', '(?P<locale>[^/]*)')

        if '{' not in self.path_format:
            if self.fingerprinted:
                fingerprint = StaticFile._create_fingerprint(self.pod, self.path_format)
                path = StaticFile.apply_fingerprint(self.path_format, fingerprint)
                concrete_paths.add(path)
            else:
                concrete_paths.add(self.path_format)

        elif 'filename' in tokens:
            # NOTE: This should be updated to support globbing directories,
            # and not simply strip all sub-paths beneath {locale}.
            source = self.source_format.replace('{filename}', '')[1:]
            source = re.sub('{locale}.*', '', source)
            source = source.rstrip('/')
            paths = self.pod.list_dir(source)
            paths = [('/' + source + path).replace(self.pod.root, '')
                     for path in paths]

            # Exclude paths matched by skip patterns.
            for pattern in SKIP_PATTERNS:
                # .gitignore-style treatment of paths without slashes.
                if '/' not in pattern:
                    pattern = '**{}**'.format(pattern)
                for skip_paths in fnmatch.filter(paths, pattern):
                    paths = [path for path in paths
                             if path.replace(self.pod.root, '') not in skip_paths]

            for pod_path in paths:
                match = re.match(source_regex, pod_path)
                # Skip adding localized paths in subfolders of other rules.
                if not self.localized and self.localization:
                    localized_source_format = self.localization['static_dir']
                    localized_source_regex = localized_source_format.replace(
                        '{filename}', '(?P<filename>.*)')
                    localized_source_regex = localized_source_regex.replace(
                        '{locale}', '(?P<locale>[^/]*)')
                    if re.match(localized_source_regex, pod_path):
                        continue
                if match:
                    kwargs = match.groupdict()
                    kwargs['root'] = self.pod.podspec.root
                    if 'fingerprint' in self.path_format:
                        fingerprint = StaticFile._create_fingerprint(self.pod, pod_path)
                        kwargs['fingerprint'] = fingerprint
                    if 'locale' in kwargs:
                        normalized_locale = self.pod.normalize_locale(kwargs['locale'])
                        kwargs['locale'] = (
                            normalized_locale.alias if normalized_locale is not None
                            else normalized_locale)
                    matched_path = self.path_format.format(**kwargs)
                    matched_path = matched_path.replace('//', '/')
                    if self.fingerprinted:
                        fingerprint = StaticFile._create_fingerprint(self.pod, pod_path)
                        matched_path = StaticFile.apply_fingerprint(matched_path, fingerprint)
                    concrete_paths.add(matched_path)

        return list(concrete_paths)


# Allow the yaml dump to write out a representation of the static file.
def static_representer(dumper, data):
    return dumper.represent_scalar(u'!g.static', data.pod_path)

yaml.SafeDumper.add_representer(StaticFile, static_representer)
