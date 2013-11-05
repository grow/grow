from apiclient import discovery
from apiclient import errors
import httplib2
import json
import requests

HOST = ''

root_url_format = '{}://{}/_ah/api'
api = 'grow'
version = 'v0.1'
errors = errors


def get_service(host=None):
  if host is None:
    host = HOST
  http_service = httplib2.Http()
  http_service.disable_ssl_certificate_validation = True
  scheme = 'http' if ':' in host else 'https'
  url = root_url_format.format(scheme, host)
  url += '/discovery/v1/apis/{api}/{apiVersion}/rest'
  service = discovery.build(api, version, http=http_service,
                            discoveryServiceUrl=url)
  return service


class Client(object):

  def __init__(self, host=None):
    self.host = host

  def rpc(self, path, body=None):
    if body is None:
      body = {}
    headers = {
        'Content-Type': 'application/json',
    }
    url = 'http://{}/_api/{}'.format(self.host, path)
    resp = requests.post(url, data=json.dumps(body), headers=headers)
    if not (resp.status_code >= 200 and resp.status_code < 205):
      raise Exception(resp.text)
    return resp


def upload_to_gcs(signed_url, file_path, content):
  files = {'file': (file_path, content)}
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
