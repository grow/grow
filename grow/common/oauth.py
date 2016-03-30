from oauth2client import client
from oauth2client import keyring_storage
from oauth2client import tools
import logging
import os

# Google API details for a native/installed application for API project grow-prod.
CLIENT_ID = '578372381550-jfl3hdlf1q5rgib94pqsctv1kgkflu1a.apps.googleusercontent.com'
CLIENT_SECRET = 'XQKqbwTg88XVpaBNRcm_tYLf'  # Not so secret for installed apps.
REDIRECT_URI = 'urn:ietf:wg:oauth:2.0:oob'

DEFAULT_STORAGE_KEY = 'Grow SDK'


def get_credentials(scope, storage_key=DEFAULT_STORAGE_KEY):
    if os.getenv('CLEAR_AUTH'):
        clear_credentials(storage_key=storage_key)
    username = os.getenv('AUTH_EMAIL_ADDRESS', 'default')
    storage = keyring_storage.Storage(storage_key, username)
    credentials = storage.get()
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
    storage = keyring_storage.Storage(storage_key, username)
    storage.delete()
