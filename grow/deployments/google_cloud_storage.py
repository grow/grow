from grow.deployments import base
from grow.pods import index
from gcloud import storage
import cStringIO
import dns.resolver
import logging
import mimetypes


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

  def __init__(self, bucket, project_id=None, email=None, key_path=None):
    self.bucket_name = bucket
    self.project_id = project_id
    self.connection = storage.get_connection(project_id, email, key_path)
    self.bucket = self.connection.get_bucket(bucket)

  def get_destination_address(self):
    return 'http://{}/'.format(self.bucket_name)

  def write_index_at_destination(self, new_index):
    self.write_file(
        index.Index.BASENAME,
        new_index.to_yaml(),
        policy='private')

  def read_file(self, path):
    file_key = self.bucket.get_key(path)

    if not file_key:
      raise IOError('File not found: {}'.format(path))

    return file_key.get_contents_as_string()

  def delete_file(self, path):
    self.bucket.delete_key(path)

  def prelaunch(self, dry_run=False):
    if dry_run:
      return
    logging.info('Configuring bucket: {}'.format(self.bucket_name))
    # acl = self.bucket.get_default_object_acl()
    # acl.all().grant_read().revoke_write()
    # acl.save()
    # self.bucket.configure_website(main_page_suffix='index.html', not_found_page='404.html')



class GoogleCloudStorageDeployment(BaseGoogleCloudStorageDeployment):
  """Deploys a pod to a static Google Cloud Storage bucket for web serving."""

  def write_file(self, path, content, policy='public-read'):
    if isinstance(content, unicode):
      content = content.encode('utf-8')

    mimetype = mimetypes.guess_type(path)[0]
    if path == 'rss/index.html':
      mimetype = 'application/xml'

    file_key = self.bucket.new_key(path)
    file_key.set_contents_from_string(content, content_type=mimetype)
