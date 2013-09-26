from boto.s3 import key
from grow.deployments import base
from grow.pods import index
import boto
import cStringIO
import dns.resolver
import logging
import mimetypes
import time


class GoogleCloudStorageDeployment(base.BaseDeployment):
  """Deploys a pod to a static Google Cloud Storage bucket for web serving."""

  CNAME = 'c.storage.googleapis.com'

  def __init__(self, bucket, access_key=None, secret=None):
    self.bucket = bucket
    self.access_key = access_key
    self.secret = secret

  def get_url(self):
    return 'http://{}/'.format(self.bucket)

  def _write_file(self, path, content, bucket=None):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    bucket_key = key.Key(bucket)
    fp = cStringIO.StringIO()
    fp.write(content)
    bucket_key.key = path.lstrip('/')
    mimetype = mimetypes.guess_type(path)[0]
    # TODO(jeremydw): Better headers.
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': mimetype,
    }
    bucket_key.set_contents_from_file(fp, headers=headers, replace=True, rewind=True, policy='public-read')
    fp.close()

  def _delete_file(self, path, bucket=None):
    bucket_key = key.Key(bucket)
    bucket_key.key = path.lstrip('/')
    bucket.delete_key(bucket_key)

  def get_deployed_index(self, bucket):
    index_key = key.Key(bucket)
    index_key.key = index.Index.BASENAME
    try:
      index_key.get_contents_as_string()
      return index.Index.from_yaml(index_key)
    except boto.exception.GSResponseError, e:
      logging.info('No index found, assuming deploying new pod.')
      if e.status != 404:
        raise
      return index.Index()

  def deploy(self, pod):
    self.test()
    start = time.time()
    logging.info('Connecting to GCS...')

    connection = boto.connect_gs(self.access_key, self.secret, is_secure=False)
    bucket = connection.get_bucket(self.bucket)

    deployed_index = self.get_deployed_index(bucket)
    paths_to_content = pod.dump()
    canary_index = index.Index()
    canary_index.update(paths_to_content)
    diffs = canary_index.diff(deployed_index)

    logging.info('Connected! Configuring bucket: {}'.format(self.bucket))
    bucket.set_acl('public-read')
    bucket.configure_versioning(False)
    bucket.configure_website(main_page_suffix='index.html', error_key='404.html')

    index.Index.apply_diffs(
        diffs, paths_to_content,
        write_func=lambda *args: self._write_file(*args, bucket=bucket),
        delete_func=lambda *args: self._delete_file(*args, bucket=bucket),
    )

    self._write_file(index.Index.BASENAME, canary_index.to_yaml(), bucket=bucket)
    logging.info('Wrote index: /{}'.format(index.Index.BASENAME))

    logging.info('Done in {}s!'.format(time.time() - start))
    logging.info('Deployed to: {}'.format(self.get_url()))

  def test(self):
    self._test_domain_cname_is_gcs()

  def _test_domain_cname_is_gcs(self):
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['8.8.8.8']  # Use Google's DNS.
    try:
      content = str(dns_resolver.query(self.bucket, 'CNAME')[0])
      is_mapped_to_gcs = content.startswith(GoogleCloudStorageDeployment.CNAME)
      if is_mapped_to_gcs:
        logging.info('Verified CNAME mapping for {} -> {}'.format(self.bucket, content))
      else:
        logging.warning(
            'CNAME mapping for {} is not GCS! Found {}, expected {}'.format(
                self.bucket, content, GoogleCloudStorageDeployment.CNAME))
    except:
      content = None
      is_mapped_to_gcs = False
      message = "Can't verify CNAME for {} is mapped to {}"
      logging.error(message.format(self.bucket, GoogleCloudStorageDeployment.CNAME))
    return is_mapped_to_gcs
