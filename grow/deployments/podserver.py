# TODO(jeremydw): Dead code.

from grow.deployments import base
from grow.client import client
import requests
import threading


class GrowServerDeployment(base.BaseDeployment):
  """Deploys a pod to a remote Grow server."""

  def __init__(self, host=None):
    self.service = client.get_service(host=host)

  def upload_pod(self, pod):
    self.stage_changeset_to_gcs(pod)

  def deploy_pod(self, pod):
    pass

  def _stage_changeset_to_gcs(self, pod):
    if not pod.changeset:
      raise ValueError('Pod must be initialized with a changeset.')

    paths = pod.list_files_in_pod()
    upload_urls = []
    for pod_path in paths:
      upload_urls.append({
          'pod': {'changeset': pod.changeset},
          'pod_path': pod_path,
      })

    print 'Starting upload...'
    body = {'upload_urls': upload_urls}
    req = self.service.pods().getUploadUrl(body=body)
    resp = req.execute()

    threads = []
    for signed_url in resp['signed_upload_urls']:
      thread = threading.Thread(
          target=GrowServerDeployment._upload_via_signed_url,
          args=(pod, signed_url))
      threads.append(thread)
      thread.start()

    for thread in threads:
      thread.join()

    print 'Finalizing...'
    req = self.service.pods().finalizeStagedFiles(body={
      'pod': {'changeset': pod.changeset}
    })
    resp = req.execute()
    print 'Upload complete.'

  @staticmethod
  def _upload_via_signed_url(pod, signed_url):
    content = pod.read_file(signed_url['pod_path'])
    files = {'file': (signed_url['pod_path'].lstrip('/'), content)}
    payload = {
        'GoogleAccessId': signed_url['google_access_id'],
        'bucket': signed_url['bucket'],
        'key': signed_url['filename'],
        'policy': signed_url['policy'],
        'signature': signed_url['signature'],
  #      'x-goog-meta-owner': signed_url['x_goog_meta_owner'],
    }
    resp = requests.post(signed_url['url'], data=payload, files=files)
    if not (resp.status_code >= 200 and resp.status_code < 205):
      raise Exception(resp.text)
    print 'Uploaded: {}'.format(signed_url['pod_path'])
