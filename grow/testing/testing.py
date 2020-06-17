"""Testing resources for grow."""

import os
import shutil
import tempfile
import unittest
from grow.pods import pods


TESTDATA_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), 'testdata'))


# root is relative to testdata/ dir
def create_test_pod_dir(root='pod'):
    dest_dir = tempfile.mkdtemp()
    dest_dir = os.path.join(dest_dir, 'test_pod')
    source_dir = os.path.join(TESTDATA_DIR, root)
    shutil.copytree(source_dir, dest_dir)
    return dest_dir


def create_test_pod(root='pod'):
    return pods.Pod(create_test_pod_dir(root))


def create_pod():
    root = tempfile.mkdtemp()
    return pods.Pod(root)


def get_testdata_dir():
    return TESTDATA_DIR


class TestCase(unittest.TestCase):
    pass

def render_path(pod, path):
    """Given a pod and a path render the path."""
    matched = pod.match(path)
    controller = pod.router.get_render_controller(
        matched.path, matched.value, params=matched.params)
    jinja_env = pod.render_pool.get_jinja_env(
        controller.doc.locale) if controller.use_jinja else None
    rendered_document = controller.render(jinja_env=jinja_env)
    return rendered_document.read()
