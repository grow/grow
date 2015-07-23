from . import base
from . import messages
from grow.pods import locales
from grow.pods import urls
import fnmatch
import mimetypes
import re

# TODO(jeremydw): Move to storage lib.
try:
  from google.appengine.ext import blobstore
except ImportError:
  blobstore = None

mimetypes.add_type('application/font-woff', '.woff')
mimetypes.add_type('image/svg+xml', '.svg')
mimetypes.add_type('text/css', '.css')


SKIP_PATTERNS = [
    '**/.**',
]


class StaticFile(object):

  def __init__(self, pod_path, serving_path, locale=None, localization=None,
               pod=None):
    self.pod = pod
    self.default_locale = pod.podspec.default_locale
    self.locale = locale or pod.podspec.default_locale
    if isinstance(self.locale, basestring):
      self.locale = locales.Locale(self.locale)
    if self.locale is not None:
      self.locale.set_alias(pod)
    self.localization = localization
    self.pod_path = pod_path
    self.serving_path = serving_path

  def __repr__(self):
    if self.locale:
      return "<StaticFile({}, locale='{}')>".format(self.pod_path, self.locale)
    return "<StaticFile({})>".format(self.pod_path)

  @property
  def url(self):
    path = self.serving_path
    return urls.Url(path=path) if path else None


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

  def get_pod_path(self):
    # If a localized file exists, serve it. Otherwise, serve the base file.
    if self.localization and '{locale}' in self.path_format:
      source_format = self.localization.get('static_dir')
      source_format += '/{filename}'
      source_format = source_format.replace('//', '/')
      pod_path = source_format.format(**self.route_params)
      if self.pod.file_exists(pod_path):
        return pod_path
    return self.source_format.format(**self.route_params)

  def render(self):
    return self.pod.read_file(self.get_pod_path())

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.get_pod_path())[0]

  def get_http_headers(self):
    path = self.pod.abs_path(self.get_pod_path())
    headers = super(StaticController, self).get_http_headers()
    if blobstore and self.pod.storage.is_cloud_storage:
      blob_key = blobstore.create_gs_key('/gs' + path)
      headers['X-AppEngine-BlobKey'] = blob_key
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
      return self.path_format.format(**match.groupdict())

  def list_concrete_paths(self):
    concrete_paths = set()
    tokens = re.findall('.?{([^}]+)}.?', self.path_format)

    source_regex = self.source_format.replace('{filename}', '(?P<filename>.*)')
    source_regex = source_regex.replace('{locale}', '(?P<locale>[^/]*)')

    if '{' not in self.path_format:
      concrete_paths.add(self.path_format)

    elif 'filename' in tokens:
      source = self.source_format.replace('{filename}', '')[1:]
      source = source.replace('{locale}', '')
      source = source.rstrip('/')
      paths = self.pod.list_dir(source)
      paths = [('/' + source + path).replace(self.pod.root, '') for path in paths]

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
        if match:
          matched_path = self.path_format.format(**match.groupdict())
          concrete_paths.add(matched_path)

    return list(concrete_paths)
