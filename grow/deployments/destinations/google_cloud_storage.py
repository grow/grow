from boto.gs import key
from . import base
from . import messages
import boto
import cStringIO
import dns.resolver
import logging
import mimetypes



class BaseGoogleCloudStorageDeploymentTestCase(base.DeploymentTestCase):

  def test_domain_cname_is_gcs(self):
    message = messages.TestResultMessage()
    message.name = 'Verify domain name is mapped to GCS.'

    CNAME = 'c.storage.googleapis.com'
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['8.8.8.8']  # Use Google's DNS.

    try:
      content = str(dns_resolver.query(self.deployment.bucket_name, 'CNAME')[0])
    except:
      text = "Can't verify CNAME for {} is mapped to {}"
      message.passed = False
      message.result = text.format(self.deployment.bucket_name, CNAME)

    if not content.startswith(CNAME):
      text = 'CNAME mapping for {} is not GCS! Found {}, expected {}'
      message.passed = False
      message.result = text.format(self.deployment.bucket_name, content, CNAME)

    return message



class BaseGoogleCloudStorageDeployment(base.BaseDeployment):

  test_case_class = BaseGoogleCloudStorageDeploymentTestCase

  def __init__(self, bucket, access_key=None, secret=None):
    self.bucket_name = bucket
    self.access_key = access_key
    self.secret = secret

  def get_destination_address(self):
    return 'http://{}/'.format(self.bucket_name)

  def write_index_at_destination(self, new_index):
    self.write_file(
        index.Index.BASENAME,
        new_index.to_yaml(),
        policy='private')

  def read_file(self, path):
    file_key = key.Key(self.bucket)
    file_key.key = path
    try:
      file_key.get_contents_as_string()
      return file_key
    except boto.exception.GSResponseError, e:
      if e.status != 404:
        raise
      raise IOError('File not found: {}'.format(path))

  def delete_file(self, path):
    bucket_key = key.Key(self.bucket)
    bucket_key.key = path.lstrip('/')
    self.bucket.delete_key(bucket_key)

  def prelaunch(self, dry_run=False):
    logging.info('Connecting to GCS...')
    connection = boto.connect_gs(self.access_key, self.secret, is_secure=False)
    self.bucket = connection.get_bucket(self.bucket_name)
    logging.info('Connected!')
    if dry_run:
      return
    logging.info('Configuring bucket: {}'.format(self.bucket_name))
    self.bucket.set_acl('public-read')
    self.bucket.configure_versioning(False)
    self.bucket.configure_website(main_page_suffix='index.html', error_key='404.html')



class GoogleCloudStorageDeployment(BaseGoogleCloudStorageDeployment):
  """Deploys a pod to a static Google Cloud Storage bucket for web serving."""

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
