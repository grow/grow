from boto.s3 import key
from . import base
from grow.deployments.indexes import indexes
import boto
import cStringIO
import logging
import mimetypes


class AmazonS3Deployment(base.BaseDeployment):

  def __init__(self, bucket, access_key=None, secret=None):
    self.bucket_name = bucket
    self.access_key = access_key
    self.secret = secret

  def get_destination_address(self):
    return 'http://{}/'.format(self.bucket_name)

  def write_index_at_destination(self, new_index):
    self.write_file(
        indexes.Index.BASENAME,
        new_index.to_yaml(),
        policy='private')

  def read_file(self, path):
    file_key = key.Key(self.bucket)
    file_key.key = path
    try:
      file_key.get_contents_as_string()
      return file_key
    except boto.exception.S3ResponseError, e:
      if e.status != 404:
        raise
      raise IOError('File not found: {}'.format(path))

  def delete_file(self, path):
    bucket_key = key.Key(self.bucket)
    bucket_key.key = path.lstrip('/')
    self.bucket.delete_key(bucket_key)

  def write_file(self, path, content, policy='public-read'):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    path = path.lstrip('/')
    bucket_key = key.Key(self.bucket)
    fp = cStringIO.StringIO()
    fp.write(content)
    bucket_key.key = path
    mimetype = mimetypes.guess_type(path)[0]
    if path == 'rss/index.html':
      mimetype = 'application/xml'
    # TODO(jeremydw): Better headers.
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': mimetype,
    }
    fp.seek(0)
    bucket_key.set_contents_from_file(fp, headers=headers, replace=True, policy=policy)
    fp.close()

  def prelaunch(self, dry_run=False):
    logging.info('Connecting to GCS...')
    connection = boto.connect_s3(self.access_key, self.secret, is_secure=False)
    self.bucket = connection.get_bucket(self.bucket_name)
    logging.info('Connected!')
    if dry_run:
      return
    logging.info('Connected! Configuring bucket: {}'.format(self.bucket_name))
    self.bucket.set_acl('public-read')
    self.bucket.configure_versioning(False)
    self.bucket.configure_website('index.html', '404.html')
