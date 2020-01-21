"""Pod storage using Google Cloud Storage as the backing."""

try:
    import cloudstorage
    from cloudstorage import cloudstorage_api
except ImportError:
    # Not running in GAE runtime.
    cloudstorage = None

try:
    from google.appengine.ext import blobstore
except ImportError:
    blobstore = None

import logging
import os
import jinja2
from grow.storage import base_storage
from grow.storage import errors


class CloudStorage(base_storage.BaseStorage):

    is_cloud_storage = True

    @staticmethod
    def open(filename, *args, **kwargs):
        if 'mode' in kwargs and kwargs['mode'] is None:
            kwargs['mode'] = 'r'
        # pylint: disable=no-member
        return cloudstorage.open(filename, *args, **kwargs)

    @staticmethod
    def read(filename):
        try:
            # pylint: disable=no-member
            return cloudstorage.open(filename).read()
        except cloudstorage.NotFoundError as e:  # pylint: disable=no-member
            logging.error(filename)
            raise IOError(str(e))

    @staticmethod
    def modified(filename):
        # pylint: disable=no-member
        return cloudstorage.stat(filename).st_ctime

    @staticmethod
    def stat(filename):
        try:
            # pylint: disable=no-member
            return cloudstorage.stat(filename)
        except cloudstorage.NotFoundError:  # pylint: disable=no-member
            raise IOError('File {} not found.'.format(filename))

    @staticmethod
    def listdir(filename, recursive=True):
        bucket, prefix = filename[1:].split('/', 1)
        bucket = '/' + bucket
        names = set()
        # pylint: disable=no-member
        for item in cloudstorage.listbucket(bucket, prefix=prefix):
            name = item.filename[len(bucket) + len(prefix) + 1:]
            if name and (recursive or '/' not in name):
                names.add(name)
        return list(names)

    @staticmethod
    def JinjaLoader(path):
        path = CloudStorage.normalize_path(path)
        return CloudStorageLoader(path)

    @staticmethod
    def normalize_path(path):
        if '..' in path:
            raise errors.PathError('".." not allowed in path: {}'.format(path))
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
        # pylint: disable=no-member
        cloudstorage.delete(path)

    @staticmethod
    def exists(filename):
        try:
            # pylint: disable=no-member
            cloudstorage.stat(filename)
            return True
        except cloudstorage.NotFoundError:  # pylint: disable=no-member
            return False

    @staticmethod
    def copy_to(path, target_path):
        return cloudstorage_api.copy2(path, target_path)

    @staticmethod
    def move_to(path, target_path):
        CloudStorage.copy_to(path, target_path)
        # pylint: disable=no-member
        cloudstorage.delete(path)

    @staticmethod
    def update_headers(headers, path):
        if blobstore is None:
            raise Exception('Cannot use blobstore outside App Engine environment.')
        # pylint: disable=no-member
        blob_key = blobstore.create_gs_key('/gs' + path)
        headers['X-AppEngine-BlobKey'] = blob_key


class CloudStorageLoader(jinja2.BaseLoader):

    def __init__(self, path):
        self.path = path

    def get_source(self, environment, template):
        path = os.path.join(self.path, template.lstrip('/'))
        try:
            source = CloudStorage.read(path)
        except cloudstorage.NotFoundError:  # pylint: disable=no-member
            raise jinja2.TemplateNotFound(template)
        # TODO(jeremydw): Make this function properly.
        source = source
        return source, path, lambda: True
