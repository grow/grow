"""Utility functions for managing the sdk."""

import os
from grow.common import system


def subprocess_args(pod, shell=False):
    """Arguments for running subprocess commands."""
    env = os.environ.copy()
    node_modules_path = os.path.join(pod.root_path, 'node_modules', '.bin')
    env['PATH'] = str(env['PATH'] + os.path.pathsep + node_modules_path)
    # TODO: Fix when the pod has environment information.
    # if pod.env and pod.env.name:
    #     env['GROW_ENVIRONMENT_NAME'] = pod.env.name
    args = {
        'cwd': pod.root_path,
        'env': env,
    }
    if shell or system.PLATFORM == 'win':
        args['shell'] = True
    return args
