import tempfile
import shutil
import os
from grow.pods import pods

_here = os.path.dirname(__file__)
TESTDATA_DIR = os.path.abspath(os.path.join(_here, 'testdata'))


def create_test_pod_dir():
    dest_dir = tempfile.mkdtemp()
    dest_dir = os.path.join(dest_dir, 'test_pod')
    source_dir = os.path.join(TESTDATA_DIR, 'pod')
    shutil.copytree(source_dir, dest_dir)
    return dest_dir


def create_test_pod():
    return pods.Pod(create_test_pod_dir())


def create_pod():
    root = tempfile.mkdtemp()
    return pods.Pod(root)


def get_testdata_dir():
    return TESTDATA_DIR
