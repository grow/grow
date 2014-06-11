from . import base
from . import messages as deployment_messages
from boto.gs import key
from boto.s3 import connection
from gcloud import storage
from protorpc import messages
import boto
import cStringIO
import dns.resolver
import logging
import mimetypes
import os
import webapp2


class TestCase(base.DestinationTestCase):

  def test_domain_cname_is_gcs(self):
    bucket_name = self.deployment.config.bucket
    CNAME = 'c.storage.googleapis.com'

    message = deployment_messages.TestResultMessage()
    message.title = 'CNAME for {} is {}'.format(bucket_name, CNAME)

    dns_resolver = dns.resolver.Resolver()
    dns_resolver.nameservers = ['8.8.8.8']  # Use Google's DNS.

    try:
      content = str(dns_resolver.query(bucket_name, 'CNAME')[0])
    except:
      text = "Can't verify CNAME for {} is mapped to {}"
      message.result = deployment_messages.Result.WARNING
      message.text = text.format(bucket_name, CNAME)
    if not content.startswith(CNAME):
      text = 'CNAME mapping for {} is not GCS! Found {}, expected {}'
      message.result = deployment_messages.Result.WARNING
      message.text = text.format(bucket_name, content, CNAME)
    else:
      text = 'CNAME for {} -> {}'.format(bucket_name, content, CNAME)
      message.text = text.format(text, content, CNAME)
    return message


class Config(messages.Message):
  bucket = messages.StringField(1)
  access_key = messages.StringField(2)
  access_secret = messages.StringField(3)
  project = messages.StringField(4)
  email = messages.StringField(5)
  key_path = messages.StringField(6)


class GoogleCloudStorageDestination(base.BaseDestination):
  NAME = 'gcs'
  TestCase = TestCase
  Config = Config

  def __str__(self):
    return 'gs://{}'.format(self.config.bucket)

  @property
  def use_interoperable_auth(self):
    return self.config.access_key is not None

  @webapp2.cached_property
  def bucket(self):
    if self.use_interoperable_auth:
      gs_connection = boto.connect_gs(
          self.config.access_key, self.config.access_secret,
          calling_format=connection.OrdinaryCallingFormat())
    else:
      gs_connection = storage.get_connection(
          self.config.project, self.config.email, self.config.key_path)
    return gs_connection.get_bucket(self.config.bucket)

  def prelaunch(self, dry_run=False):
    if dry_run:
      return
    logging.info('Configuring GS bucket: {}'.format(self.config.bucket))
    if self.use_interoperable_auth:
      self.bucket.set_acl('public-read')
      self.bucket.configure_versioning(False)
      self.bucket.configure_website(main_page_suffix='index.html', error_key='404.html')
    else:
      acl = self.bucket.get_default_object_acl()
      acl.all().grant_read().revoke_write()
      acl.save()
      self.bucket.configure_website(main_page_suffix='index.html', not_found_page='404.html')

  def write_control_file(self, path, content):
    path = os.path.join(self.control_dir, path.lstrip('/'))
    return self.write_file(path, content, policy='private')

  def read_file(self, path):
    if self.use_interoperable_auth:
      file_key = key.Key(self.bucket)
      file_key.key = path
      try:
        return file_key.get_contents_as_string()
      except boto.exception.GSResponseError, e:
        if e.status != 404:
          raise
        raise IOError('File not found: {}'.format(path))
    else:
      file_key = self.bucket.get_key(path)
      if not file_key:
        raise IOError('File not found: {}'.format(path))
      return file_key.get_contents_as_string()

  def delete_file(self, path):
    if self.use_interoperable_auth:
      file_key = key.Key(self.bucket)
      file_key.key = path.lstrip('/')
      self.bucket.delete_key(file_key)
    else:
      self.bucket.delete_key(path)

  def write_file(self, path, content, policy='public-read'):
    if isinstance(content, unicode):
      content = content.encode('utf-8')
    path = path.lstrip('/')
    mimetype = mimetypes.guess_type(path)[0]
    fp = cStringIO.StringIO()
    fp.write(content)
    size = fp.tell()

    try:
      if self.use_interoperable_auth:
        file_key = key.Key(self.bucket)
        file_key.key = path
        headers = {'Cache-Control': 'no-cache'}  # TODO(jeremydw): Better headers.
        if mimetype:
          headers['Content-Type'] = mimetype
        file_key.set_contents_from_file(fp, headers=headers, replace=True, policy=policy,
                                        size=size, rewind=True)
      else:
        file_key = self.bucket.new_key(path)
        file_key.set_contents_from_file(fp, content_type=mimetype, size=size, rewind=True)
        if policy == 'private':
          acl = file_key.get_acl()
          acl.all().revoke_read().revoke_write()
          file_key.save_acl(acl)
    finally:
      fp.close()
