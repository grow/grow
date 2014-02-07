import os
from grow.pods.storage.google_storage import *
from grow.pods.storage.errors import *
from grow.pods.storage.file_storage import *

if 'APPENGINE_RUNTIME' in os.environ:
  auto = CloudStorage
else:
  auto = FileStorage
