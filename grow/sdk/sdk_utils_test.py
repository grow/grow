"""Tests for SDK Utils."""

import os
import unittest
from grow.common import base_config
from grow.pods import env as environment
from grow.pods import pods
from grow import storage
from grow.sdk import sdk_utils
from grow.testing import testing


class SdkUtilsTestCase(unittest.TestCase):
    """Test the SDK Utils."""

    def setUp(self):
        self.config = base_config.BaseConfig()
        self.dir_path = testing.create_test_pod_dir()
        self.pod = pods.Pod(self.dir_path, storage=storage.FileStorage)

    def test_subprocess_args(self):
        """Test subprocess args."""
        args = sdk_utils.subprocess_args(self.pod)
        ending = os.path.join('node_modules', '.bin')
        self.assertTrue(args['env']['PATH'].endswith(ending))
        self.assertFalse('GROW_ENVIRONMENT_NAME' in args['env'])

    def test_subprocess_args_env_name(self):
        """Test subprocess args env name."""
        self.pod.set_env(environment.Env(environment.EnvConfig(name='testing')))
        args = sdk_utils.subprocess_args(self.pod)
        self.assertEqual(args['env']['GROW_ENVIRONMENT_NAME'], 'testing')

    def test_subprocess_shell(self):
        """Test subprocess args with shell."""
        args = sdk_utils.subprocess_args(self.pod, shell=True)
        self.assertTrue(args['shell'])
