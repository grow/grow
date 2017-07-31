"""Common OAuth functionality."""

import os

# Silence "Loading" messages from keyring.
import logging
log = logging.getLogger('keyring.backend')
log.setLevel(logging.WARNING)

from oauth2client import client
from oauth2client import service_account
from oauth2client import tools

try:
    from oauth2client.contrib import appengine
except ImportError:
    appengine = None


# Google API details for a native/installed application for API project grow-prod.
CLIENT_ID = '578372381550-jfl3hdlf1q5rgib94pqsctv1kgkflu1a.apps.googleusercontent.com'
CLIENT_SECRET = 'XQKqbwTg88XVpaBNRcm_tYLf'  # Not so secret for installed apps.
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
DEFAULT_STORAGE_KEY = 'Grow SDK'
BROWSER_API_KEY = 'AIzaSyDCb_WtWJnlLPdL8IGLvcVhXAjaBHbRY5E'

_CLEARED_AUTH_KEYS = {}

DEFAULT_AUTH_KEY_FILE = 'auth-key.json'


def get_storage(key, username):
    """Returns the Storage class compatible with the current environment."""
    if appengine:
        return appengine.StorageByKeyName(
            appengine.CredentialsModel, username, 'credentials')
    from oauth2client.contrib import keyring_storage
    return keyring_storage.Storage(key, username)


def get_credentials_and_storage(scope, storage_key=DEFAULT_STORAGE_KEY):
    if os.getenv('CLEAR_AUTH') and storage_key not in _CLEARED_AUTH_KEYS:
        clear_credentials(storage_key=storage_key)
    username = os.getenv('AUTH_EMAIL_ADDRESS', 'default')
    storage = get_storage(storage_key, username)
    if 'CI' in os.environ:  # Avoid using keyring in CI/Travis.
        return None, storage
    credentials = storage.get()
    return credentials, storage


def get_or_create_credentials(scope, storage_key=DEFAULT_STORAGE_KEY):
    key_file = os.getenv('AUTH_KEY_FILE')
    # If AUTH_KEY_FILE is unset, use default auth key file if it exists.
    if not key_file and os.path.exists(DEFAULT_AUTH_KEY_FILE):
        key_file = DEFAULT_AUTH_KEY_FILE
    if key_file:
        key_file = os.path.expanduser(key_file)
        return (service_account.
            ServiceAccountCredentials.from_json_keyfile_name(key_file, scope))
    if appengine:
        return appengine.AppAssertionCredentials(scope)
    credentials, storage = get_credentials_and_storage(scope,
        storage_key=storage_key)
    if credentials is None:
        parser = tools.argparser
        if os.getenv('INTERACTIVE_AUTH'):
            args = []
        else:
            args = ['--noauth_local_webserver']
        flags, _ = parser.parse_known_args(args)
        flow = client.OAuth2WebServerFlow(CLIENT_ID, CLIENT_SECRET, scope,
                                          redirect_uri=REDIRECT_URI)
        credentials = tools.run_flow(flow, storage, flags)
        # run_flow changes the logging level, so change it back.
        logging.getLogger().setLevel(getattr(logging, 'INFO'))
    return credentials


def clear_credentials(storage_key=DEFAULT_STORAGE_KEY):
    username = os.getenv('AUTH_EMAIL_ADDRESS', 'default')
    storage = get_storage(storage_key, username)
    storage.delete()
    _CLEARED_AUTH_KEYS[storage_key] = True
