from grow.deployments import base
from grow.pods import index
import boto
import cStringIO
import dns.resolver
import logging
import mimetypes
import multiprocessing
import threading
from gslib.third_party.oauth2_plugin import oauth2_plugin
from gslib.third_party.oauth2_plugin import oauth2_client

try:
  oauth2_client.token_exchange_lock = multiprocessing.Manager().Lock()
except:
  oauth2_client.token_exchange_lock = threading.Lock()


# URI scheme for Google Cloud Storage.
GOOGLE_STORAGE = 'gs'
# URI scheme for accessing local files.
LOCAL_FILE = 'file'


class BaseGoogleCloudStorageDeploymentTestCase(base.DeploymentTestCase):

  def test_domain_cname_is_gcs(self):
    CNAME = 'c.storage.googleapis.com'
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['8.8.8.8']  # Use Google's DNS.

    try:
      content = str(dns_resolver.query(self.deployment.bucket_name, 'CNAME')[0])
    except:
      text = "Can't verify CNAME for {} is mapped to {}"
      self.fail(text.format(self.deployment.bucket_name, CNAME))

    if not content.startswith(CNAME):
      text = 'CNAME mapping for {} is not GCS! Found {}, expected {}'
      self.fail(text.format(self.deployment.bucket_name, content, CNAME))



class BaseGoogleCloudStorageDeployment(base.BaseDeployment):

  test_case_class = BaseGoogleCloudStorageDeploymentTestCase

  def __init__(self, bucket, project_id=None):
    self.bucket_name = bucket
    self.bucket_uri = boto.storage_uri(bucket, GOOGLE_STORAGE)
    self.project_id = project_id

  def get_destination_address(self):
    return 'http://{}/'.format(self.bucket_name)

  def write_index_at_destination(self, new_index):
    self.write_file(
        index.Index.BASENAME,
        new_index.to_yaml(),
        policy='private')

  def read_file(self, path):
    path = path.lstrip('/')
    file_uri = boto.storage_uri(self.bucket_name + '/' + path, GOOGLE_STORAGE)
    object_contents = cStringIO.StringIO()

    try:
      file_uri.get_key().get_file(object_contents)
      return object_contents
    except boto.exception.GSResponseError, e:
      if e.status != 404:
        raise
      raise IOError('File not found: {}'.format(path))

  def delete_file(self, path):
    file_uri = boto.storage_uri(self.bucket_name + '/' + path, GOOGLE_STORAGE)
    file_uri.delete()

  def prelaunch(self, dry_run=False):
    if dry_run:
      return
    logging.info('Configuring bucket: {}'.format(self.bucket_name))
    # print dir(self.bucket_uri)
    self.bucket_uri.set_acl('public-read')
    self.bucket_uri.configure_versioning(False)
    self.bucket_uri.set_website_config(main_page_suffix='index.html', error_key='404.html')



class GoogleCloudStorageDeployment(BaseGoogleCloudStorageDeployment):
  """Deploys a pod to a static Google Cloud Storage bucket for web serving."""

  def write_file(self, path, content, policy='public-read'):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    path = path.lstrip('/')
    file_uri = boto.storage_uri(self.bucket_name + '/' + path, GOOGLE_STORAGE)
    fp = cStringIO.StringIO()
    fp.write(content)
    mimetype = mimetypes.guess_type(path)[0]
    if path == 'rss/index.html':
      mimetype = 'application/xml'
    # TODO(jeremydw): Better headers.
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': mimetype,
    }
    fp.seek(0)
    file_uri.new_key().set_contents_from_file(fp, headers=headers, replace=True, policy=policy)
    fp.close()
