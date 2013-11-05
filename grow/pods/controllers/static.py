import mimetypes
import os
import re
from grow.pods.controllers import base

try:
  from google.appengine.ext import blobstore
except ImportError:
  blobstore = None

mimetypes.add_type('application/font-woff', '.woff')


class StaticController(base.BaseController):

  KIND = 'Static file'

  def __init__(self, path_format, source_format=None, pod=None):
    self.path_format = path_format.replace('<grow:', '{').replace('>', '}')
    self.source_format = source_format.replace('<grow:', '{').replace('>', '}')
    self.pod = pod
    self.route_params = {}

  def get_pod_path(self):
    return self.source_format.format(**self.route_params)

  def render(self):
    return self.pod.read_file(self.get_pod_path())

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.get_pod_path())[0]

  def get_http_headers(self):
    headers = super(StaticController, self).get_http_headers()
    if blobstore and self.pod.storage.is_cloud_storage:
      path = self.get_pod_path().lstrip('/')
      path = '/gs' + os.path.join(self.pod.root, path)
      headers['X-AppEngine-BlobKey'] = blobstore.create_gs_key(path)
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
      for path in paths:
        for filename in re.findall(source_regex, path):
          params = {'filename': filename}
          concrete_paths.add(self.path_format.format(**params))

    return list(concrete_paths)
