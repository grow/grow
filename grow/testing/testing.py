import tempfile
import shutil
import os
from grow.pods import pods

_here = os.path.dirname(__file__)
TESTDATA_DIR = os.path.abspath(os.path.join(_here, 'testdata'))


# pod_dir is relative to testdata/ dir
def create_test_pod_dir(pod_dir='pod'):
    dest_dir = tempfile.mkdtemp()
    dest_dir = os.path.join(dest_dir, 'test_pod')
    source_dir = os.path.join(TESTDATA_DIR, pod_dir)
    shutil.copytree(source_dir, dest_dir)
    return dest_dir


def create_test_pod(pod_dir='pod'):
    return pods.Pod(create_test_pod_dir(pod_dir))


def get_testdata_dir():
    return TESTDATA_DIR
