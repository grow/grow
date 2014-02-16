from boto.s3 import key
from grow.deployments import base
from grow.pods import index
from grow.common import utils
import boto
import cStringIO
import dns.resolver
import logging
import mimetypes
import time


class BaseGoogleCloudStorageDeployment(base.BaseDeployment):

  CNAME = 'c.storage.googleapis.com'

  def get_url(self):
    return 'http://{}/'.format(self.bucket_name)

  @classmethod
  def get_deployed_index(cls, bucket):
    index_key = key.Key(bucket)
    index_key.key = index.Index.BASENAME
    try:
      index_key.get_contents_as_string()
      logging.info('Loaded index from GCS.')
      return index.Index.from_yaml(index_key)
    except boto.exception.GSResponseError, e:
      logging.info('No index found, assuming deploying new pod.')
      if e.status != 404:
        raise
      return index.Index()

  def delete_file(self, path, bucket=None):
    bucket_key = key.Key(bucket)
    bucket_key.key = path.lstrip('/')
    bucket.delete_key(bucket_key)

  def test(self):
    self._test_domain_cname_is_gcs()

  def _test_domain_cname_is_gcs(self):
    CNAME = BaseGoogleCloudStorageDeployment.CNAME
    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['8.8.8.8']  # Use Google's DNS.
    try:
      content = str(dns_resolver.query(self.bucket_name, 'CNAME')[0])
      is_mapped_to_gcs = content.startswith(CNAME)
      if is_mapped_to_gcs:
        logging.info('Verified CNAME mapping for {} -> {}'.format(self.bucket_name, content))
      else:
        logging.warning(
            'CNAME mapping for {} is not GCS! Found {}, expected {}'.format(
                self.bucket_name, content, CNAME))
    except:
      content = None
      is_mapped_to_gcs = False
      message = "Can't verify CNAME for {} is mapped to {}"
      logging.error(message.format(self.bucket_name, CNAME))
    return is_mapped_to_gcs


class GoogleCloudStorageDeployment(BaseGoogleCloudStorageDeployment):
  """Deploys a pod to a static Google Cloud Storage bucket for web serving."""

  def set_params(self, bucket, access_key=None, secret=None):
    self.bucket_name = bucket
    self.access_key = access_key
    self.secret = secret

  def _write_file(self, path, content, bucket=None, policy='public-read'):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    path = path.lstrip('/')
    bucket_key = key.Key(bucket)
    fp = cStringIO.StringIO()
    fp.write(content)
    bucket_key.key = path
    mimetype = mimetypes.guess_type(path)[0]
    if path == 'rss/index.html':
      mimetype = 'application/xml'
#    elif mimetype is None:
#      mimetype = 'text/html'
    # TODO(jeremydw): Better headers.
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': mimetype,
    }
    # bucket_key.connection.debug = 1
    fp.seek(0)
    bucket_key.set_contents_from_file(fp, headers=headers, replace=True, policy=policy)
    fp.close()

  def deploy(self, pod, dry_run=False):
    self.test()
    start = time.time()
    logging.info('Connecting to GCS...')

    connection = boto.connect_gs(self.access_key, self.secret, is_secure=False)
    bucket = connection.get_bucket(self.bucket_name)

    logging.info('Connected! Configuring bucket: {}'.format(self.bucket_name))

    deployed_index = self.get_deployed_index(bucket)
    paths_to_content = pod.dump()

    canary_index = index.Index()
    canary_index.update(paths_to_content)

    diffs = canary_index.diff(deployed_index)

    if not dry_run:
      bucket.set_acl('public-read')
      bucket.configure_versioning(False)
      bucket.configure_website(main_page_suffix='index.html', error_key='404.html')

      if not diffs:
        logging.info('Nothing to launch, aborted.')
        return

      if self.confirm:
        print
        diffs.log_pretty()
        print
        choice = utils.interactive_confirm('Proceed with launch?')
        if not choice:
          return

      index.Index.apply_diffs(
          diffs, paths_to_content,
          write_func=lambda *args: self._write_file(*args, bucket=bucket),
          delete_func=lambda *args: self.delete_file(*args, bucket=bucket),
      )

      self._write_file(
          index.Index.BASENAME,
          canary_index.to_yaml(),
          bucket=bucket,
          policy='private')
      logging.info('Wrote index: /{}'.format(index.Index.BASENAME))

    logging.info('Done in {}s!'.format(time.time() - start))
    logging.info('Deployed to: {}'.format(self.get_url()))

    return diffs
