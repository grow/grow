from . import base
from boto import auth_handler
from boto.gs import key
from boto.s3 import connection
from gcs_oauth2_boto_plugin import oauth2_client
from gcs_oauth2_boto_plugin import oauth2_helper
from grow.common import oauth
from grow.common import utils
from grow.pods import env
from grow.rendering import rendered_document
from protorpc import messages
import boto
import cStringIO
import gcs_oauth2_boto_plugin
import httplib2
import logging
import mimetypes
import os


OAUTH_SCOPE = 'https://www.googleapis.com/auth/devstorage.full_control'
STORAGE_KEY = 'Grow SDK - Google Cloud Storage'


class FieldMessage(messages.Message):
    name = messages.StringField(1)
    value = messages.StringField(2)


class HeaderMessage(messages.Message):
    extensions = messages.StringField(1, repeated=True)
    fields = messages.MessageField(FieldMessage, 2, repeated=True)


class Config(messages.Message):
    bucket = messages.StringField(1)
    access_key = messages.StringField(2)
    access_secret = messages.StringField(3)
    env = messages.MessageField(env.EnvConfig, 7)
    keep_control_dir = messages.BooleanField(8, default=False)
    redirect_trailing_slashes = messages.BooleanField(9, default=True)
    main_page_suffix = messages.StringField(10, default='index.html')
    not_found_page = messages.StringField(11, default='404.html')
    oauth2 = messages.BooleanField(12, default=False)
    headers = messages.MessageField(HeaderMessage, 13, repeated=True)


class GoogleCloudStorageDestination(base.BaseDestination):
    KIND = 'gcs'
    Config = Config

    def __str__(self):
        return 'gs://{}'.format(self.config.bucket)

    @utils.cached_property
    def bucket(self):
        if self.config.oauth2:
            enable_oauth2_auth_handler()
        gs_connection = boto.connect_gs(
            self.config.access_key, self.config.access_secret,
            calling_format=connection.OrdinaryCallingFormat())
        # Always use our internal cacerts.txt file. This fixes an issue with the
        # PyInstaller-based frozen distribution, while allowing us to continue to
        # verify certificates and use a secure connection.
        gs_connection.ca_certificates_file = utils.get_cacerts_path()
        try:
            return gs_connection.get_bucket(self.config.bucket)
        except boto.exception.GSResponseError as e:
            if e.status == 404:
                logging.info('Creating bucket: {}'.format(self.config.bucket))
                return gs_connection.create_bucket(self.config.bucket)
            raise

    def dump(self, pod, use_threading=True):
        pod.set_env(self.get_env())
        return pod.dump(
            suffix=self.config.main_page_suffix,
            append_slashes=self.config.redirect_trailing_slashes, use_threading=use_threading)

    def prelaunch(self, dry_run=False):
        if dry_run:
            return
        logging.info('Configuring GCS bucket: {}'.format(self.config.bucket))
        self.bucket.configure_website(
            main_page_suffix=self.config.main_page_suffix,
            error_key=self.config.not_found_page)

    def write_control_file(self, path, content):
        path = os.path.join(self.control_dir, path.lstrip('/'))
        return self.write_file(
            rendered_document.RenderedDocument(path, content), policy='private')

    def read_file(self, path):
        file_key = key.Key(self.bucket)
        file_key.key = path
        try:
            return file_key.get_contents_as_string()
        except boto.exception.GSResponseError as e:
            if e.status != 404:
                raise
            raise IOError('File not found: {}'.format(path))

    def delete_file(self, path):
        file_key = key.Key(self.bucket)
        file_key.key = path.lstrip('/')
        self.bucket.delete_key(file_key)

    def write_file(self, rendered_doc, policy='public-read'):
        path = rendered_doc.path
        content = rendered_doc.read()
        path = path.lstrip('/')
        path = path if path != '' else self.config.main_page_suffix
        fp = cStringIO.StringIO()
        fp.write(content)
        size = fp.tell()
        try:
            file_key = key.Key(self.bucket)
            file_key.key = path
            headers = self._get_headers_for_path(path)
            file_key.set_contents_from_file(
                fp, headers=headers, replace=True, policy=policy, size=size,
                rewind=True)
        finally:
            fp.close()

    def _get_headers_for_path(self, path):
        mimetype = mimetypes.guess_type(path)[0] or 'text/html'
        ext = os.path.splitext(path)[-1] or '.html'
        headers = {}
        headers['Content-Type'] = mimetype
        if self.config.headers and not path.startswith('.grow'):
            for header in self.config.headers:
                if (ext not in header.extensions
                        and '*' not in header.extensions):
                    continue
                for field in header.fields:
                    headers[field.name] = field.value
        else:
            # Use legacy default.
            headers['Cache-Control'] = 'no-cache'
        return headers


# NOTE: Here be demons. We monkeypatch several methods in Google's oauth2 boto
# plugin in order to leverage Grow's standard "OAuth2WebServerFlow". This permits
# permits the user to grant Grow access to their Google Cloud Storage through the
# oauth2 dance, rather than requiring the user to create a $HOME/.boto file and
# copy and paste access keys and secrets or run "gsutil config" prior to performing
# a GCS deployment. We may want to send a PR to
# https://github.com/GoogleCloudPlatform/gcs-oauth2-boto-plugin to add an option
# to permit this flow, since there's nothing special about the flow and Grow.


def enable_oauth2_auth_handler():
    # TODO: Monkeypatching to enable flow-based auth isn't threadsafe. This should
    # be adjusted so each deployment can customize whether they want to use
    # flow-based auth.
    class PatchedOAuth2Auth(auth_handler.AuthHandler):

        capability = ['google-oauth2', 's3']

        def __init__(self, path, config, provider):
            self.oauth2_client = None
            if (provider.name == 'google'):
                if config.has_option('GoogleCompute', 'service_account'):
                    self.oauth2_client = oauth2_client.CreateOAuth2GCEClient()
                else:
                    self.oauth2_client = oauth2_helper.OAuth2ClientFromBotoConfig(
                        config)
                    self.oauth2_client.cache_key_base = oauth.CLIENT_ID
            if not self.oauth2_client:
                raise auth_handler.NotReadyToAuthenticate()

        def add_auth(self, http_request):
            header = self.oauth2_client.GetAuthorizationHeader()
            http_request.headers['Authorization'] = header

    # Ensure our refresh token is set in the boto config.
    if not boto.config.has_section('Credentials'):
        boto.config.add_section('Credentials')
    credentials = patched_get_credentials()
    # Boto can't refresh this properly, so just do it every time.
    credentials.refresh(httplib2.Http())
    refresh_token = credentials.refresh_token
    boto.config.set('Credentials', 'gs_oauth2_refresh_token', refresh_token)

    # Do the monkeypatching.
    Client = oauth2_client.OAuth2UserAccountClient
    Client.GetCredentials = patched_get_credentials
    Client.FetchAccessToken = patched_fetch_access_token
    gcs_oauth2_boto_plugin.oauth2_plugin.OAuth2Auth = PatchedOAuth2Auth


def patched_get_credentials(*args):
    """Gets credentials from Grow's flow."""
    return oauth.get_or_create_credentials(scope=OAUTH_SCOPE, storage_key=STORAGE_KEY)


def patched_fetch_access_token(self):
    """Uses credentials from Grow's flow to retrieve an access token."""
    credentials = self.GetCredentials()
    return oauth2_client.AccessToken(credentials.access_token,
                                     credentials.token_expiry, datetime_strategy=self.datetime_strategy)


gcs_oauth2_boto_plugin.SetFallbackClientIdAndSecret(
    oauth.CLIENT_ID, oauth.CLIENT_SECRET)
