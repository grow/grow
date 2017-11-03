"""Utility functions for managing the sdk."""

import os
import platform
from grow.common import config


VERSION = config.VERSION
PLATFORM = None
if 'Linux' in platform.system():
    PLATFORM = 'linux'
elif 'Darwin' in platform.system():
    PLATFORM = 'mac'
elif 'Windows' in platform.system():
    PLATFORM = 'win'


def subprocess_args(pod, shell=False):
    """Arguments for running subprocess commands."""
    env = os.environ.copy()
    node_modules_path = os.path.join(pod.root, 'node_modules', '.bin')
    env['PATH'] = str(env['PATH'] + os.path.pathsep + node_modules_path)
    if pod.env and pod.env.name:
        env['GROW_ENVIRONMENT_NAME'] = pod.env.name
    args = {
        'cwd': pod.root,
        'env': env,
    }
    if shell or PLATFORM == 'win':
        args['shell'] = True
    return args
