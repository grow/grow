from grow.pods.storage import base_storage
import errno
import shutil
import jinja2
import os


def _normalize(filename):
  if filename.startswith('/_grow'):
    filename = filename[1:]
    filename = os.path.abspath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..', '..', 'growedit'))
  return filename


class FileStorage(base_storage.BaseStorage):

  @staticmethod
  def open(filename, mode=None):
    if mode is None:
      mode = 'r'
    filename = _normalize(filename)
    return open(filename, mode=mode)

  @staticmethod
  def read(filename):
    filename = _normalize(filename)
    return open(filename).read()

  @staticmethod
  def modified(filename):
    filename = _normalize(filename)
    return os.stat(filename).st_mtime

  @staticmethod
  def stat(filename):
    filename = _normalize(filename)
    return os.stat(filename)

  @staticmethod
  def listdir(dirpath):
    dirpath = _normalize(dirpath)
    paths = []
    for root, dirs, files in os.walk(dirpath):
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
    filename = _normalize(filename)
    return os.remove(filename)

  @staticmethod
  def delete_dir(dirpath):
    dirpath = _normalize(dirpath)
    shutil.rmtree(dirpath)

  @staticmethod
  def copy_to(paths, target_paths):
    # TODO(jeremydw): Rename to bulk_copy_to.
    for i, path in enumerate(paths):
      target_path = target_paths[i]
      shutil.copyfile(path, target_path)
      shutil.copystat(path, target_path)

  @staticmethod
  def move_to(path, target_path):
    os.rename(path, target_path)
