import base64
import json
import md5
import mimetypes
import requests


class Launchpad(object):

  def __init__(self, host):
    self.host = host
    self.gcs_session = GoogleStorageSigningSession()

  def rpc(self, path, body=None):
    if body is None:
      body = {}
    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/_api/{}'.format(self.host, path)
    resp = requests.post(url, data=json.dumps(body), headers=headers)
    if not (resp.status_code >= 200 and resp.status_code < 205):
      raise Exception(resp.text)
    return resp.json()

  def create_fileset(self, pod):
    podspec = pod.get_podspec()
    config = podspec.get_config()
    project_id = config['project']
    owner, project = project_id.split('/')
    fileset = {
        'name': 'master',
        'project': {
            'nickname': project,
            'owner': {'nickname': owner}
        },
    }
    paths_to_contents = pod.dump()

    for path, content in paths_to_contents.iteritems():
      if isinstance(content, unicode):
        paths_to_contents[path] = content.encode('utf-8')

    print 'Signing requests for {} files.'.format(len(paths_to_contents))
    sign_requests_request = self.gcs_session.create_sign_requests_request(
        fileset, paths_to_contents)
    resp = self.rpc('filesets.sign_requests', sign_requests_request)
    print 'Retrieved signed requests.'

    # retrieve signed requests.
    # upload files via signed requests.
    for req in resp['signed_requests']:
      file_path = req['file_path']
      print 'Uploading {}'.format(file_path)
      self.gcs_session.execute_signed_upload(req, paths_to_contents[file_path])


class GoogleStorageSigningSession(object):

  @staticmethod
  def create_unsigned_request(verb, path, content=None):
    req = {
      'file_path': path,
      'verb': verb,
    }
    if verb == 'PUT':
      mimetype = mimetypes.guess_type(path)[0]
      md5_digest = base64.b64encode(md5.new(content).digest())
      req['headers'] = {}
      req['headers']['content_length'] = str(len(content))
      req['headers']['content_md5'] = md5_digest
      if mimetype:
        req['headers']['content_type'] = mimetype
    return req

  def create_sign_requests_request(self, fileset, paths_to_contents):
    unsigned_requests = []
    for path, content in paths_to_contents.iteritems():
      req = self.create_unsigned_request('PUT', path, content)
      unsigned_requests.append(req)
    return {
        'fileset': fileset,
        'unsigned_requests': unsigned_requests,
    }

  @staticmethod
  def execute_signed_upload(signed_request, content):
    req = signed_request
    params = {
        'GoogleAccessId': req['params']['google_access_id'],
        'Signature': req['params']['signature'],
        'Expires': req['params']['expires'],
    }
    headers = {
        'Content-Type': req['headers']['content_type'],
        'Content-MD5': req['headers']['content_md5'],
        'Content-Length': req['headers']['content_length'],
    }
    resp = requests.put(req['url'], params=params, headers=headers, data=content)
    if not (resp.status_code >= 200 and resp.status_code < 205):
      raise Exception(resp.text)
    return resp
