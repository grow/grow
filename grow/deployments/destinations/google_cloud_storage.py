from . import base
from . import messages as deployment_messages
from ..indexes import indexes
from boto.gs import key
from protorpc import messages
import boto
import cStringIO
import dns.resolver
import logging
import mimetypes
import webapp2


class Config(messages.Message):
  project = messages.StringField(1)
  bucket = messages.StringField(2)
  access_key = messages.StringField(3)
  access_secret = messages.StringField(4)


class TestCase(base.DeploymentTestCase):

  def test_domain_cname_is_gcs(self):
    message = deployment_messages.TestResultMessage()
    message.title = 'Domain CNAME is mapped to Google Cloud Storage'

    CNAME = 'c.storage.googleapis.com'
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['8.8.8.8']  # Use Google's DNS.

    bucket_name = self.deployment.config.bucket
    try:
      content = str(dns_resolver.query(bucket_name, 'CNAME')[0])
    except:
      text = "Can't verify CNAME for {} is mapped to {}"
      message.result = deployment_messages.Result.WARNING
      message.text = text.format(bucket_name, CNAME)

    if not content.startswith(CNAME):
      text = 'CNAME mapping for {} is not GCS! Found {}, expected {}'
      message.result = deployment_messages.Result.WARNING
      message.text = text.format(bucket_name, content, CNAME)
    else:
      text = 'CNAME for {} -> {}'.format(bucket_name, content, CNAME)
      message.text = text.format(text, content, CNAME)

    return message


class GoogleCloudStorageDeployment(base.BaseDeployment):
  NAME = 'gcs'
  TestCase = TestCase
  Config = Config

  def get_destination_address(self):
    return 'http://{}/'.format(self.config.bucket)

  def write_index_at_destination(self, new_index):
    self.write_file(
        self.get_index_path(),
        indexes.Index.to_string(new_index),
        policy='private')

  def read_file(self, path):
    file_key = key.Key(self.bucket)
    file_key.key = path
    try:
      return file_key.get_contents_as_string()
    except boto.exception.GSResponseError, e:
      if e.status != 404:
        raise
      raise IOError('File not found: {}'.format(path))

  def delete_file(self, path):
    bucket_key = key.Key(self.bucket)
    bucket_key.key = path.lstrip('/')
    self.bucket.delete_key(bucket_key)

  @webapp2.cached_property
  def bucket(self):
    connection = boto.connect_gs(self.config.access_key,
                                 self.config.access_secret,
                                 is_secure=False)
    return connection.get_bucket(self.config.bucket)

  def prelaunch(self, dry_run=False):
    logging.info('Connected to GCS bucket: {}'.format(self.config.bucket))
    if dry_run:
      return
    logging.info('Setting bucket\'s ACLs and website configuration.')
    self.bucket.set_acl('public-read')
    self.bucket.configure_versioning(False)
    self.bucket.configure_website(main_page_suffix='index.html', error_key='404.html')

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
