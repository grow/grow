"""Local file storage."""

import errno
import hashlib
import os
import shutil
from grow.storage import base_storage
from grow.templates import jinja_loader


class FileStorage(base_storage.BaseStorage):

    @staticmethod
    def open(filename, mode=None):
        if mode is None:
            mode = 'r'
        return open(filename, mode=mode)

    @staticmethod
    def read(filename):
        try:
            with open(filename) as fp:
                content = fp.read()
        except UnicodeDecodeError as e:
            with open(filename, 'rb') as fp:
                content = fp.read()
        return content

    @staticmethod
    def modified(filename):
        return os.stat(filename).st_mtime

    @staticmethod
    def size(filename):
        return os.path.getsize(filename)

    @staticmethod
    def stat(filename):
        return os.stat(filename)

    @staticmethod
    def hash(filename):
        hash_digest = hashlib.sha256()
        with open(filename, "rb") as source_file:
            for chunk in iter(lambda: source_file.read(4096), b""):
                hash_digest.update(chunk)
        return hash_digest.hexdigest()

    @staticmethod
    def listdir(dirpath, recursive=True):
        paths = []
        for root, _, files in os.walk(dirpath, topdown=True, followlinks=True):
            for filename in files:
                path = os.path.join(root, filename)[len(dirpath):]
                paths.append(path)
            # if not recursive, break after walking top-level dir
            if not recursive:
                break
        return paths

    @staticmethod
    def walk(dirpath):
        return os.walk(dirpath, followlinks=True)

    @staticmethod
    def JinjaLoader(path):
        return jinja_loader.FrontMatterLoader(path)

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
        try:
            with cls.open(path, mode='w') as fp:
                fp.write(content)
        except TypeError:
            with cls.open(path, mode='wb') as fp:
                fp.write(content)

    @staticmethod
    def exists(filename):
        return os.path.exists(filename)

    @staticmethod
    def delete(filename):
        return os.remove(filename)

    @staticmethod
    def delete_dir(dirpath):
        shutil.rmtree(dirpath)

    @staticmethod
    def delete_files(dirpaths, recursive=False, pattern=None):
        """Delete files from within the dirpaths that match a pattern."""
        for dirpath in dirpaths:
            for root, _, files in os.walk(dirpath, followlinks=True):
                for filename in files:
                    if not pattern or pattern.search(filename):
                        os.remove(os.path.join(root, filename))
                if not recursive:
                    break

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
