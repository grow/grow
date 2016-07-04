from . import base
from grow.common import utils as common_utils
from boto.s3 import connection
from boto.s3 import key
from grow.pods import env
from protorpc import messages
import boto
import cStringIO
import logging
import os
import mimetypes


class Config(messages.Message):
    bucket = messages.StringField(1)
    access_key = messages.StringField(2)
    access_secret = messages.StringField(3)
    env = messages.MessageField(env.EnvConfig, 4)
    keep_control_dir = messages.BooleanField(5, default=False)
    redirect_trailing_slashes = messages.BooleanField(6, default=True)
    index_document = messages.StringField(7, default='index.html')
    error_document = messages.StringField(8, default='404.html')



class AmazonS3Destination(base.BaseDestination):
    KIND = 's3'
    Config = Config

    def __str__(self):
        return 's3://{}'.format(self.config.bucket)

    @common_utils.cached_property
    def bucket(self):
        boto_connection = boto.connect_s3(
            self.config.access_key, self.config.access_secret,
            calling_format=connection.OrdinaryCallingFormat())
        return boto_connection.get_bucket(self.config.bucket)
        try:
            return boto_connection.get_bucket(self.config.bucket)
        except boto.exception.S3ResponseError as e:
            if e.status == 404:
                logging.info('Creating bucket: {}'.format(self.config.bucket))
                return boto_connection.create_bucket(self.config.bucket)
            raise

    def dump(self, pod):
        pod.env = self.get_env()
        return pod.dump(
            suffix=self.config.index_document,
            append_slashes=self.config.redirect_trailing_slashes)

    def prelaunch(self, dry_run=False):
        if dry_run:
            return
        logging.info('Configuring S3 bucket: {}'.format(self.config.bucket))
        self.bucket.configure_website(
            self.config.index_document,
            self.config.error_document)

    def write_control_file(self, path, content):
        path = os.path.join(self.control_dir, path.lstrip('/'))
        return self.write_file(path, content, policy='private')

    def read_file(self, path):
        file_key = key.Key(self.bucket)
        file_key.key = path
        try:
            return file_key.get_contents_as_string()
        except boto.exception.S3ResponseError, e:
            if e.status != 404:
                raise
            raise IOError('File not found: {}'.format(path))

    def delete_file(self, path):
        bucket_key = key.Key(self.bucket)
        bucket_key.key = path.lstrip('/')
        self.bucket.delete_key(bucket_key)

    def write_file(self, path, content, policy='public-read'):
        path = path.lstrip('/')
        path = path if path != '' else self.config.index_document
        if isinstance(content, unicode):
            content = content.encode('utf-8')
        bucket_key = key.Key(self.bucket)
        bucket_key.key = path
        fp = cStringIO.StringIO()
        fp.write(content)
        mimetype = mimetypes.guess_type(path)[0]
        # TODO: Allow configurable headers.
        headers = {
            'Cache-Control': 'no-cache',
            'Content-Type': mimetype if mimetype else 'text/html',
        }
        fp.seek(0)
        bucket_key.set_contents_from_file(fp, headers=headers, replace=True, policy=policy)
        fp.close()
