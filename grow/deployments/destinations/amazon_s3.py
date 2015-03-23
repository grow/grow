from . import base
from boto.s3 import connection
from boto.s3 import key
from grow.pods import env
from protorpc import messages
import boto
import cStringIO
import logging
import os
import mimetypes
import webapp2


class Config(messages.Message):
  bucket = messages.StringField(1)
  access_key = messages.StringField(2)
  access_secret = messages.StringField(3)
  env = messages.MessageField(env.EnvConfig, 4)
  keep_control_dir = messages.BooleanField(5, default=False)


class AmazonS3Destination(base.BaseDestination):
  KIND = 's3'
  Config = Config

  def __str__(self):
    return 's3://{}'.format(self.config.bucket)

  @webapp2.cached_property
  def bucket(self):
    boto_connection = boto.connect_s3(
        self.config.access_key, self.config.access_secret,
        calling_format=connection.OrdinaryCallingFormat())
    return boto_connection.get_bucket(self.config.bucket)

  def prelaunch(self, dry_run=False):
    if dry_run:
      return
    logging.info('Configuring S3 bucket: {}'.format(self.config.bucket))
    self.bucket.set_acl('public-read')
    self.bucket.configure_versioning(False)
    self.bucket.configure_website('index.html', '404.html')

  def write_control_file(self, path, content):
    path = os.path.join(self.control_dir, path.lstrip('/'))
    return self.write_file(path, content, policy='private')

  def read_file(self, path, buildsuffix=''):
    if buildsuffix:
      if path.endswith(buildsuffix):
        path = path[:-len(buildsuffix)]
    file_key = key.Key(self.bucket)
    file_key.key = path
    try:
      return file_key.get_contents_as_string()
    except boto.exception.S3ResponseError, e:
      if e.status != 404:
        raise
      raise IOError('File not found: {}'.format(path))

  def delete_file(self, path, buildsuffix=''):
    if buildsuffix:
      if path.endswith(buildsuffix):
        path = path[:-len(buildsuffix)]
    bucket_key = key.Key(self.bucket)
    bucket_key.key = path.lstrip('/')
    self.bucket.delete_key(bucket_key)

  def write_file(self, path, content, policy='public-read', buildsuffix=''):
    path = path.lstrip('/')
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    bucket_key = key.Key(self.bucket)
    bucket_key.key = path
    fp = cStringIO.StringIO()
    fp.write(content)
    # TODO(jeremydw): Better headers.
    mimetype = mimetypes.guess_type(path)[0]
    headers = {'Cache-Control': 'no-cache'}
    if mimetype:
      headers['Content-Type'] = mimetype
    if buildsuffix:
      if path.endswith(buildsuffix):
        bucket_key.key = path[:-len(buildsuffix)]
    fp.seek(0)
    bucket_key.set_contents_from_file(fp, headers=headers, replace=True, policy=policy)
    fp.close()
