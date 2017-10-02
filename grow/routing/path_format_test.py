"""Tests for the path formatter."""

import unittest
import mock
from grow.routing import path_format as grow_path_format

def _mock_env(fingerprint=None):
    env = mock.Mock()
    prop_fingerprint = mock.PropertyMock(return_value=fingerprint)
    type(env).fingerprint = prop_fingerprint
    return env

def _mock_pod(podspec=None, env=None):
    pod = mock.Mock()
    if not podspec:
        podspec = {}
    prop_podspec = mock.PropertyMock(return_value=podspec)
    type(pod).podspec = prop_podspec
    if not env:
        env = _mock_env()
    type(pod).env = mock.PropertyMock(return_value=env)
    return pod

class PathFormatTestCase(unittest.TestCase):
    """Test the routes."""

    def test_format_pod_root(self):
        """Tests that pod paths are formatted correctly."""
        pod = _mock_pod(podspec={
            'root': 'root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test', path_format.format_pod('/{root}/test'))

    def test_format_pod_env_fingerprint(self):
        """Tests that env fingerprints are formatted correctly."""
        env = _mock_env(fingerprint="ABC123")
        pod = _mock_pod(env=env)
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/ABC123/test', path_format.format_pod('/{env.fingerprint}/test'))

    def test_format_pod_extra_slash(self):
        """Tests that extra slashes are removed."""
        pod = _mock_pod(podspec={
            'root': '/root_path',
        })
        path_format = grow_path_format.PathFormat(pod)
        self.assertEquals(
            '/root_path/test', path_format.format_pod('/{root}/test'))


if __name__ == '__main__':
    unittest.main()
