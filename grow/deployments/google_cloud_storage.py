from boto.s3 import key
from grow.deployments import base
import boto
import cStringIO
import mimetypes
import threading


class GoogleCloudStorageDeployment(base.BaseDeployment):
  """Deploys a pod to a static Google Cloud Storage bucket for web serving."""

  def __init__(self, bucket, access_key=None, secret=None):
    self.bucket = bucket
    self.access_key = access_key
    self.secret = secret

  def deploy_static_pod(self, pod):
    connection = boto.connect_gs(self.access_key, self.secret, is_secure=False)
    bucket = connection.get_bucket(self.bucket)
    bucket.set_acl('public-read')
    bucket.configure_versioning(False)
    bucket.configure_website(main_page_suffix='index.html', error_key='404.html')

    paths_to_contents = self.pod.dump()
    for path, contents in paths_to_contents.iteritems():
      if isinstance(contents, unicode):
        contents = contents.encode('utf-8')
      bucket_key = key.Key(bucket)
      fp = cStringIO.StringIO()
      fp.write(contents)
      bucket_key.key = path.lstrip('/')
      mimetype = mimetypes.guess_type(path)[0]
      headers = {
          'Cache-Control': 'no-cache',
          'Content-Type': mimetype,
      }
      bucket_key.set_contents_from_file(fp, headers=headers, replace=True, rewind=True, policy='public-read')
      fp.close()
