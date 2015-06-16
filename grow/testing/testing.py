import tempfile
import shutil
import os

_here = os.path.dirname(__file__)
TESTDATA_DIR = os.path.join(_here, '..', 'pods', 'testdata', 'pod')


def create_test_pod_dir():
  dir_path = tempfile.mkdtemp()
  dir_path = os.path.join(dir_path, 'pod')
  shutil.copytree(TESTDATA_DIR, dir_path)
  return dir_path
