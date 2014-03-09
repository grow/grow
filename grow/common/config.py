import os
import sys

try:
  from google.appengine.api import app_identity
  _appid = app_identity.get_application_id()
except (ImportError, AttributeError):
  app_identity = None
  _appid = ''

BUCKET = '{}-grow'.format(_appid)
if os.environ.get('SERVER_SOFTWARE', '').startswith('Dev'):
  BUCKET = 'dev-{}'.format(BUCKET)

# Holds one directory per changeset.
PODS_DIR = '/{}/pods'.format(BUCKET)

# Holds routing tree.
LIVE_PODS_FILE = '/{}/live_pods'.format(BUCKET)

# Maps pod names to changesets.
CHANGESETS_DIR = '/{}/changesets'.format(BUCKET)

GCS_API_URL = 'https://{}.commondatastorage.googleapis.com'.format(BUCKET)

GROWSPACE_DOMAINS = ()

PREVIEW_DOMAINS = (
    'growlaunches.com',
)

try:
  VERSION = open(os.path.join(sys._MEIPASS, 'VERSION')).read().strip()
except AttributeError:
  VERSION = open(os.path.join(os.path.dirname(__file__), '..', 'VERSION')).read().strip()
