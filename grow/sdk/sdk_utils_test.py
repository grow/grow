"""Tests for SDK Utils."""

import os
import unittest
from grow.common import base_config
from grow.sdk import sdk_utils
from grow.testing import mocks


class SdkUtilsTestCase(unittest.TestCase):
    """Test the SDK Utils."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        env = mocks.mock_env(name="testing")
        self.pod = mocks.mock_pod(env=env, root_path='/testing/')

    def test_subprocess_args(self):
        """Test subprocess args."""
        args = sdk_utils.subprocess_args(self.pod)
        ending = os.path.join('node_modules', '.bin')
        self.assertTrue(args['env']['PATH'].endswith(ending))

    # TODO: Add back when the environment is part of the pod.
    # def test_subprocess_args_env_name(self):
    #     """Test subprocess args env name."""
    #     args = sdk_utils.subprocess_args(self.pod)
    #     self.assertEqual(args['env']['GROW_ENVIRONMENT_NAME'], 'testing')

    def test_subprocess_args_no_env_name(self):
        """Test subprocess args without env name."""
        pod = mocks.mock_pod(root_path='/testing/')
        args = sdk_utils.subprocess_args(pod)
        self.assertFalse('GROW_ENVIRONMENT_NAME' in args['env'])

    def test_subprocess_shell(self):
        """Test subprocess args with shell."""
        args = sdk_utils.subprocess_args(self.pod, shell=True)
        self.assertTrue(args['shell'])
