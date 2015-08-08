from . import base
from . import messages
from grow.pods import locales
from grow.pods import urls
import fnmatch
import mimetypes
import re
import webob
import webapp2

mimetypes.add_type('application/font-woff', '.woff')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('text/css', '.css')


SKIP_PATTERNS = [
    '**/.**',
]


class StaticFile(object):

  def __init__(self, pod_path, serving_path, locale=None, localization=None,
               controller=None, pod=None):
    self.pod = pod
    self.default_locale = pod.podspec.default_locale
    self.locale = pod.normalize_locale(locale)
    self.localization = localization
    self.pod_path = pod_path
    self.serving_path = serving_path
    self.controller = controller

  def __repr__(self):
    if self.locale:
      return "<StaticFile({}, locale='{}')>".format(self.pod_path, self.locale)
    return "<StaticFile({})>".format(self.pod_path)

  @property
  def url(self):
    serving_path = self.serving_path
    path_format = self.controller.path_format.replace('{filename}', '')
    suffix = serving_path.replace(path_format, '')
    if self.localization:
      localized_pod_path = self.localization['static_dir'] + suffix
      localized_pod_path = localized_pod_path.format(locale=self.locale)
      if self.pod.file_exists(localized_pod_path):
        # Internal paths use Babel locales, serving paths use aliases.
        locale = self.locale.alias if self.locale is not None else self.locale
        localized_serving_path = self.localization['serve_at'] + suffix
        localized_serving_path = localized_serving_path.format(locale=locale)
        serving_path = localized_serving_path
    return urls.Url(path=serving_path) if serving_path else None


class StaticController(base.BaseController):
  KIND = messages.Kind.STATIC

  def __init__(self, path_format, source_format=None, localized=False,
               localization=None, pod=None):
    # path_format: "serve_at"
    # source_format: "static_dir"
    self.path_format = path_format.replace('<grow:', '{').replace('>', '}')
    self.source_format = source_format.replace('<grow:', '{').replace('>', '}')
    self.pod = pod
    self.localized = localized
    self.localization = localization
    self.route_params = {}

  def __repr__(self):
    return '<Static(format=\'{}\')>'.format(self.source_format)

  def get_localized_pod_path(self):
    if (self.localization
        and '{locale}' in self.localization['static_dir']
        and 'locale' in self.route_params):
      source_format = self.localization['serve_at']
      source_format += '/{filename}'
      source_format = source_format.replace('//', '/')
      kwargs = self.route_params
      if 'locale' in kwargs:
        locale = locales.Locale.from_alias(self.pod, kwargs['locale'])
        kwargs['locale'] = str(locale)
      pod_path = source_format.format(**kwargs)
      if self.pod.file_exists(pod_path):
        return pod_path

  def get_pod_path(self):
    # If a localized file exists, serve it. Otherwise, serve the base file.
    return (self.get_localized_pod_path()
            or self.source_format.format(**self.route_params))

  def validate(self):
    if not self.pod.file_exists(self.get_pod_path()):
      path = self.get_pod_path()
      message = '"{}" could not be found in the pod.'.format(path)
      raise webob.exc.HTTPNotFound(message)

  def render(self):
    return self.pod.read_file(self.get_pod_path())

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.get_pod_path())[0]

  def get_http_headers(self):
    path = self.pod.abs_path(self.get_pod_path())
    headers = super(StaticController, self).get_http_headers()
    self.pod.storage.update_headers(headers, path)
    modified = str(self.pod.storage.modified(path))
    headers['Last-Modified'] = modified.split('.')[0]
    headers['Cache-Control'] = 'max-age'
    return headers

  def match_pod_path(self, pod_path):
    if self.path_format == pod_path:
      return self.path_format
    tokens = re.findall('.?{([^>]+)}.?', self.path_format)
    if 'filename' in tokens:
      source_regex = self.source_format.replace('{filename}', '(?P<filename>.*)')
      source_regex = source_regex.replace('{locale}', '(?P<locale>[^/]*)')
      match = re.match(source_regex, pod_path)
      if match:
        kwargs = match.groupdict()
        if 'locale' in kwargs:
          kwargs['locale'] = str(
              locales.Locale.from_alias(self.pod, kwargs['locale']))
        return self.path_format.format(**kwargs)

  def list_concrete_paths(self):
    concrete_paths = set()
    tokens = re.findall('.?{([^}]+)}.?', self.path_format)

    source_regex = self.source_format.replace('{filename}', '(?P<filename>.*)')
    source_regex = source_regex.replace('{locale}', '(?P<locale>[^/]*)')

    if '{' not in self.path_format:
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

      for path in paths:
        match = re.match(source_regex, path)
        # Skip adding localized paths in subfolders of other rules.
        if not self.localized and self.localization:
          localized_source_format = self.localization['static_dir']
          localized_source_regex = localized_source_format.replace(
              '{filename}', '(?P<filename>.*)')
          localized_source_regex = localized_source_regex.replace(
              '{locale}', '(?P<locale>[^/]*)')
          if re.match(localized_source_regex, path):
            continue
        if match:
          kwargs = match.groupdict()
          if 'locale' in kwargs:
            normalized_locale = self.pod.normalize_locale(kwargs['locale'])
            kwargs['locale'] = (
                normalized_locale.alias if normalized_locale is not None
                else normalized_locale)
          matched_path = self.path_format.format(**kwargs)
          concrete_paths.add(matched_path)

    return list(concrete_paths)
