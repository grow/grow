from boto.s3 import key
from grow.deployments import base
import boto
import cStringIO
import dns.resolver
import logging
import mimetypes
import threading
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

  def _upload(self, bucket, path, contents):
    if isinstance(contents, unicode):
      contents = contents.encode('utf-8')
    logging.info('Uploading {}...'.format(path))
    bucket_key = key.Key(bucket)
    fp = cStringIO.StringIO()
    fp.write(contents)
    bucket_key.key = path.lstrip('/')
    mimetype = mimetypes.guess_type(path)[0]
    # TODO(jeremydw): Better headers.
    headers = {
        'Cache-Control': 'no-cache',
        'Content-Type': mimetype,
    }
    bucket_key.set_contents_from_file(fp, headers=headers, replace=True, rewind=True, policy='public-read')
    fp.close()

  def deploy(self, pod):
    self.test_domain_cname_is_gcs()
    start = time.time()
    logging.info('Connecting to GCS...')
    # TODO(jeremydw): Read manifest and takedown old content here.
    connection = boto.connect_gs(self.access_key, self.secret, is_secure=False)
    bucket = connection.get_bucket(self.bucket)
    logging.info('Connected! Configuring bucket: {}'.format(self.bucket))
    bucket.set_acl('public-read')
    bucket.configure_versioning(False)
    bucket.configure_website(main_page_suffix='index.html', error_key='404.html')
    paths_to_contents = pod.dump()
    # TODO(jeremydw): Thread pool.
    threads = []
    for path, contents in paths_to_contents.iteritems():
      thread = threading.Thread(target=self._upload, args=(bucket, path, contents))
      threads.append(thread)
      thread.start()
    for thread in threads:
      thread.join()
    logging.info('Done in {}s!'.format(time.time() - start))
    logging.info('Deployed to: {}'.format(self.get_url()))

  def test(self):
    pass
    self.test_bucket_cname()

  def test_domain_cname_is_gcs(self):
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
