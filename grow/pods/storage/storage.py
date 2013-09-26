try:
  from grow.lib import cloudstorage
except:
  cloudstorage = None

# TODO(jeremydw): There's a bunch of ugly stuff in this file and 
# it should be fixed.
import os
if not 'SERVER_SOFTWARE' in os.environ:
  cloudstorage = None

import jinja2
import errno
import logging



class Error(Exception):
  pass


class PathError(Error, ValueError):
  pass


if cloudstorage:
  NotFoundError = cloudstorage.NotFoundError
#  class NotFoundError(Error, IOError, cloudstorage.NotFoundError):
#    pass
else:
  class NotFoundError(Error, IOError):
    pass


class BaseStorage(object):

  is_cloud_storage = False

  @staticmethod
  def read(filename):
    raise NotImplementedError

  @staticmethod
  def open(filename, mode='r'):
    raise NotImplementedError

  @staticmethod
  def modified(filename):
    raise NotImplementedError

  @staticmethod
  def stat(filename):
    raise NotImplementedError

  @staticmethod
  def listdir(dirpath):
    raise NotImplementedError

  @staticmethod
  def JinjaLoader(path):
    raise NotImplementedError

  @classmethod
  def write(cls, path, content):
    file_obj = cls.open(path, mode='w')
    file_obj.write(content)
    return file_obj


def normalize_path(filename):
  if filename.startswith('/_grow'):
    filename = filename[1:]
  return filename


class FileStorage(BaseStorage):

  @staticmethod
  def open(filename, mode=None):
    if mode is None:
      mode = 'r'
    filename = normalize_path(filename)
    return open(filename, mode=mode)

  @staticmethod
  def read(filename):
    filename = normalize_path(filename)
    return open(filename).read()

  @staticmethod
  def modified(filename):
    filename = normalize_path(filename)
    return os.stat(filename).st_mtime

  @staticmethod
  def stat(filename):
    filename = normalize_path(filename)
    return os.stat(filename)

  @staticmethod
  def listdir(dirpath):
    dirpath = normalize_path(dirpath)
    paths = []
    for root, dirs, files in os.walk(dirpath):
      if '.git' in root:
        continue
      for filename in files:
        path = os.path.join(root, filename)[len(dirpath):]
        paths.append(path)
    return paths

  @staticmethod
  def JinjaLoader(path):
    return jinja2.FileSystemLoader(path)

  @classmethod
  def write(cls, path, content):
    dirname = os.path.dirname(path)
    try:
      os.makedirs(dirname)
    except OSError as e:
      if e.errno == errno.EEXIST and os.path.isdir(dirname):
        pass
      else:
        raise
    return cls.open(path, mode='w').write(content)

  @staticmethod
  def exists(filename):
    return os.path.exists(filename)

  @staticmethod
  def delete(filename):
    filename = normalize_path(filename)
    return os.remove(filename)


class CloudStorage(BaseStorage):

  is_cloud_storage = True

  @staticmethod
  def open(filename, *args, **kwargs):
    return cloudstorage.open(filename, *args, **kwargs)

  @staticmethod
  def read(filename):
    try:
      return cloudstorage.open(filename).read()
    except cloudstorage.NotFoundError as e:
      logging.error(filename)
      raise IOError(str(e))

  @staticmethod
  def modified(filename):
    return cloudstorage.stat(filename).st_ctime

  @staticmethod
  def stat(filename):
    try:
      return cloudstorage.stat(filename)
    except cloudstorage.NotFoundError:
      raise IOError('File {} not found.'.format(filename))

  @staticmethod
  def listdir(filename):
    bucket, prefix = filename[1:].split('/', 1)
    bucket = '/' + bucket
    names = set()
    for item in cloudstorage.listbucket(bucket, prefix=prefix):
      name = item.filename[len(bucket) + len(prefix) + 1:]
      if name:
        names.add(name)
    return list(names)

  @staticmethod
  def JinjaLoader(path):
    path = CloudStorage.normalize_path(path)
    return CloudStorageLoader(path)

  @staticmethod
  def normalize_path(path):
    if '..' in path:
      raise PathError('".." not allowed in path: {}'.format(path))
    if not path.startswith('/'):
      return '/' + path
    return path

  @classmethod
  def write(cls, path, content):
    path = CloudStorage.normalize_path(path)
    file_obj = cls.open(path, mode='w')
    file_obj.write(content)
    file_obj.close()
    return file_obj

  @classmethod
  def delete(cls, path):
    path = CloudStorage.normalize_path(path)
    cloudstorage.delete(path)

  @staticmethod
  def exists(filename):
    try:
      cloudstorage.stat(filename)
      return True
    except cloudstorage.NotFoundError:
      return False


class CloudStorageLoader(jinja2.BaseLoader):

  def __init__(self, path):
    self.path = path

  def get_source(self, environment, template):
    path = os.path.join(self.path, template)
    try:
      source = CloudStorage.read(path)
    except cloudstorage.NotFoundError:
      raise jinja2.TemplateNotFound(template)
    # TODO(jeremydw): Fix this ugly crap.
    source = source.decode('utf-8')
    return source, path, lambda: True
#    return source, path, lambda: mtime == CloudStorage.modified(path)


auto = CloudStorage if cloudstorage else FileStorage
