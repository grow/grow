"""Common OAuth functionality."""

import logging
import os
import socket

from grow.common import utils

# Silence "Loading" messages from keyring.
# Even though we are not using keyring it is part of the oauth library.
KEYRING_LOG = logging.getLogger('keyring.backend')
KEYRING_LOG.setLevel(logging.WARNING)

logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)


# Google API details for a native/installed application for API project grow-prod.
CLIENT_ID = os.getenv(
    'GROW_OAUTH_CLIENT_ID',
    '578372381550-jfl3hdlf1q5rgib94pqsctv1kgkflu1a.apps.googleusercontent.com',
)
CLIENT_SECRET = os.getenv(
    'GROW_OAUTH_CLIENT_SECRET',
    'XQKqbwTg88XVpaBNRcm_tYLf',  # Not so secret for installed apps.
)
REDIRECT_URI = 'http://localhost:8080/'
DEFAULT_STORAGE_KEY = 'Grow SDK'
BROWSER_API_KEY = 'AIzaSyDCb_WtWJnlLPdL8IGLvcVhXAjaBHbRY5E'

_LAST_LOGGED_EMAIL = None
_CLEARED_AUTH_KEYS = {}

DEFAULT_AUTH_KEY_FILE = 'auth-key.json'

OOB_GUIDANCE_MESSAGE = (
    'Google has deprecated the out-of-band (OOB) copy-paste OAuth flow.\n'
    'To authenticate:\n'
    '  1. Interactive (recommended): Run with the default localhost browser flow '
    '(omit `--no-interactive-auth` / `NO_INTERACTIVE_AUTH`).\n'
    '  2. Headless / CI / SSH: Use a service account JSON key via '
    '`--auth-key-file path/to/auth-key.json` (or `AUTH_KEY_FILE`), '
    'or place `auth-key.json` in your pod root.\n'
    '  3. Stale token errors: Run `grow --clear-auth` to clear cached credentials.'
)


def _find_available_port(preferred_ports=(8080, 8090)):
    """Return an available localhost port, preferring standard OAuth ports."""
    for port in preferred_ports:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            if sock.connect_ex(('localhost', port)) != 0:
                return port
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('localhost', 0))
        return sock.getsockname()[1]


def get_storage(key, username):
    """Returns the Storage class compatible with the current environment."""
    from oauth2client import file as oauth_file

    key = utils.slugify(key)
    file_name = os.path.expanduser(f'~/.config/grow/{key}_{username}')
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
    from oauth2client import client, service_account, tools

    key_file = os.getenv('AUTH_KEY_FILE')
    # If AUTH_KEY_FILE is unset, use default auth key file if it exists.
    if not key_file and os.path.exists(DEFAULT_AUTH_KEY_FILE):
        key_file = DEFAULT_AUTH_KEY_FILE
    if key_file:
        key_file = os.path.expanduser(key_file)
        return service_account.ServiceAccountCredentials.from_json_keyfile_name(key_file, scope)
    credentials, storage = get_credentials_and_storage(scope, storage_key=storage_key)
    if credentials is None:
        if os.getenv('NO_INTERACTIVE_AUTH'):
            raise RuntimeError(
                'Non-interactive OAuth requested without a service account key.\n'
                f'{OOB_GUIDANCE_MESSAGE}'
            )
        port = _find_available_port()
        parser = tools.argparser
        flags, _ = parser.parse_known_args(['--auth_host_port', str(port)])
        flow = client.OAuth2WebServerFlow(
            CLIENT_ID, CLIENT_SECRET, scope, redirect_uri=f'http://localhost:{port}/'
        )
        try:
            credentials = tools.run_flow(flow, storage, flags)
        except client.HttpAccessTokenRefreshError as err:
            raise client.HttpAccessTokenRefreshError(f'{err}\n\n{OOB_GUIDANCE_MESSAGE}') from err
        except SystemExit as err:
            raise RuntimeError(
                f'OAuth authentication failed ({err}).\n\n{OOB_GUIDANCE_MESSAGE}'
            ) from err
        # run_flow changes the logging level, so change it back.
        logging.getLogger().setLevel(logging.INFO)
    # Avoid logspam by logging the email address only once.
    if hasattr(credentials, 'id_token') and credentials.id_token:
        email = credentials.id_token.get('email')
        global _LAST_LOGGED_EMAIL
        if email and _LAST_LOGGED_EMAIL != email:
            logging.info(f'Authorizing using -> {email}')
            _LAST_LOGGED_EMAIL = email
    return credentials


def clear_credentials(storage_key=DEFAULT_STORAGE_KEY):
    username = os.getenv('AUTH_EMAIL_ADDRESS', 'default')
    storage = get_storage(storage_key, username)
    storage.delete()
    _CLEARED_AUTH_KEYS[storage_key] = True
