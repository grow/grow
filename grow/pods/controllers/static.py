from . import base
from . import messages
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


class StaticController(base.BaseController):
  KIND = messages.Kind.STATIC

  def __init__(self, path_format, source_format=None, pod=None):
    # path_format: "serve_at"
    # source_format: "static_dir"
    self.path_format = path_format.replace('<grow:', '{').replace('>', '}')
    self.source_format = source_format.replace('<grow:', '{').replace('>', '}')
    self.pod = pod
    self.route_params = {}

  def __repr__(self):
    return '<Static(format=\'{}\')>'.format(self.source_format)

  def get_pod_path(self):
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

  def list_concrete_paths(self):
    concrete_paths = set()
    tokens = re.findall('.?{([^>]+)}.?', self.path_format)

    if '{' not in self.path_format:
      concrete_paths.add(self.path_format)

    elif 'filename' in tokens:
      source = self.source_format.replace('{filename}', '')[1:]
      source_regex = self.source_format.replace('{filename}', '(.*)')

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
        for filename in re.findall(source_regex, path):
          params = {'filename': filename}
          concrete_paths.add(self.path_format.format(**params))

    return list(concrete_paths)
