# TODO(jeremydw): This is currently broken.
# TODO(jeremydw): Rename to: "GoogleCloudStorageCopierDeployment"

import datetime
import os
from grow.common import config
from grow.pods import index
from grow.deployments import google_cloud_storage
import boto
import logging
import mimetypes



class GoogleStorageFromAppEngineDeployment(
    google_cloud_storage.BaseGoogleCloudStorageDeployment):

  def set_params(self, bucket_name, source_keys, dest_keys):
    self.bucket_name = bucket_name
    self.source_keys = source_keys
    self.dest_keys = dest_keys

  def deploy(self, pod, dry_run=False):
    source_connection = boto.connect_gs(self.source_keys[0], self.source_keys[1])
    source_bucket = source_connection.get_bucket(config.BUCKET)

    dest_connection = boto.connect_gs(self.dest_keys[0], self.dest_keys[1])
    dest_bucket = dest_connection.get_bucket(self.bucket_name)

    paths_to_content = pod.dump()
    deployed_index = google_cloud_storage.GoogleCloudStorageDeployment.get_deployed_index(dest_bucket)

    canary_index = index.Index()
    canary_index.update(paths_to_content)
    diffs = canary_index.diff(deployed_index)

    root = os.path.abspath(
        os.path.join(pod.root, '..', 'builds', datetime.datetime.now().strftime('%Y-%m-%d.%H%M%S')))

    if not dry_run:
      dest_bucket.configure_versioning(False)
      dest_bucket.configure_website(main_page_suffix='index.html', error_key='404.html')
      dest_bucket.set_acl('public-read')

      index.Index.apply_diffs(
          diffs, paths_to_content,
          write_func=lambda *args: self._write_file(
              *args, pod=pod, root=root, source_bucket=source_bucket,
              dest_bucket=dest_bucket),
          delete_func=lambda *args: self.delete_file(
              *args, source_bucket=source_bucket, dest_bucket=dest_bucket),
      )
      self._write_file(
          index.Index.BASENAME,
          canary_index.to_yaml(),
          pod=pod,
          root=root,
          source_bucket=source_bucket,
          dest_bucket=dest_bucket,
          policy='private')
      logging.info('Wrote index: /{}'.format(index.Index.BASENAME))

    return diffs

  def _write_file(self, path, content, pod=None, root=None, source_bucket=None, dest_bucket=None, policy='public-read'):
    path = path.lstrip('/')

    # Write temp file to Grow's GCS.
    source_path = os.path.join(root, path)
    pod.storage.write(source_path, content)

    # TODO: Better cache headers.
    headers = {
        'x-goog-acl': policy,
        'Cache-Control': 'no-cache',
    }

    mimetype = mimetypes.guess_type(path)[0]
    metadata = {}
    if mimetype:
      headers['Content-Type'] = mimetype
      metadata['Content-Type'] = mimetype
    logging.info('Copying to production GCS: {}/{}'.format(config.BUCKET, path))
    source_path = source_path.lstrip('/')
    source_path = '/'.join(source_path.split('/')[1:])  # Pop the bucket off.
    dest_bucket.copy_key(path.lstrip('/'), config.BUCKET, source_path, headers=headers, metadata=metadata)
