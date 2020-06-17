"""Common OAuth functionality."""

import logging
import os

from grow.common import utils
from oauth2client import client
from oauth2client import file as oauth_file
from oauth2client import service_account
from oauth2client import tools

# Silence "Loading" messages from keyring.
# Even though we are not using keyring it is part of the oauth library.
KEYRING_LOG = logging.getLogger('keyring.backend')
KEYRING_LOG.setLevel(logging.WARNING)

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


# Google API details for a native/installed application for API project grow-prod.
CLIENT_ID = '578372381550-jfl3hdlf1q5rgib94pqsctv1kgkflu1a.apps.googleusercontent.com'
CLIENT_SECRET = 'XQKqbwTg88XVpaBNRcm_tYLf'  # Not so secret for installed apps.
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'
DEFAULT_STORAGE_KEY = 'Grow SDK'
BROWSER_API_KEY = 'AIzaSyDCb_WtWJnlLPdL8IGLvcVhXAjaBHbRY5E'

_LAST_LOGGED_EMAIL = None
_CLEARED_AUTH_KEYS = {}

DEFAULT_AUTH_KEY_FILE = 'auth-key.json'


def get_storage(key, username):
    """Returns the Storage class compatible with the current environment."""
    key = utils.slugify(key)
    file_name = os.path.expanduser('~/.config/grow/{}_{}'.format(key, username))
    dir_name = os.path.dirname(file_name)
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)
    return oauth_file.Storage(file_name)


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
    # Avoid logspam by logging the email address only once.
    if hasattr(credentials, 'id_token') and credentials.id_token:
        email = credentials.id_token.get('email')
        global _LAST_LOGGED_EMAIL
        if email and _LAST_LOGGED_EMAIL != email:
            logging.info('Authorizing using -> {}'.format(email))
            _LAST_LOGGED_EMAIL = email
    return credentials


def clear_credentials(storage_key=DEFAULT_STORAGE_KEY):
    username = os.getenv('AUTH_EMAIL_ADDRESS', 'default')
    storage = get_storage(storage_key, username)
    storage.delete()
    _CLEARED_AUTH_KEYS[storage_key] = True
