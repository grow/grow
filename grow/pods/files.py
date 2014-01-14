from grow.common import utils
from grow.pods import messages
import mimetypes
import os

mimetypes.add_type('text/plain', '.md')
mimetypes.add_type('text/plain', '.yaml')
mimetypes.add_type('text/plain', '.yml')

try:
  from google.appengine.ext import blobstore
except ImportError:
  blobstore = None


class Error(Exception):
  pass


class FileDoesNotExistError(Error):
  pass


class File(object):

  def __init__(self, pod_path, pod):
    utils.validate_name(pod_path)
    self.pod_path = pod_path
    self.pod = pod

  @classmethod
  def create(cls, pod_path, content, pod):
    file_obj = cls(pod_path, pod)
    file_obj.update_content(content)
    return file_obj

  @classmethod
  def get(cls, pod_path, pod):
    file_obj = cls(pod_path, pod)
    file_obj.get_content()
#      raise FileDoesNotExistError('"{}" does not exist.'.format(pod_path))
    return file_obj

  @property
  def mimetype(self):
    return mimetypes.guess_type(self.pod_path)[0]

  @classmethod
  def list(cls, pod, prefix='/'):
    paths = sorted(pod.list_dir(prefix))
    return [File(path, pod) for path in paths]

  def delete(self):
    return self.pod.delete_file(self.pod_path)

  def move_to(self, dest_pod_path):
    self.pod.move_file_to(self.pod_path, dest_pod_path)

  def get_content(self):
    try:
      return self.pod.read_file(self.pod_path)
    except IOError as e:
      raise FileDoesNotExistError(e)

  def update_content(self, content):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    if content is None:
      content = ''
    self.pod.write_file(self.pod_path, content)

  def get_http_headers(self):
    headers = {}
    if self.mimetype:
      headers['Content-Type'] = self.mimetype
    if blobstore and self.pod.storage.is_cloud_storage:
      pod_path = self.pod_path.lstrip('/')
      root = '/' + self.pod.root.lstrip('/')
      path = '/gs' + os.path.join(root, pod_path)
      headers['X-AppEngine-BlobKey'] = blobstore.create_gs_key(path)
    return headers

  def to_message(self):
    message = messages.FileMessage()
    message.pod_path = self.pod_path
    message.mimetype = self.mimetype
    return message
