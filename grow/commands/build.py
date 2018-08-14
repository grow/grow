"""Build pods into static deployments."""

import os
import click
from grow.commands import result
from grow.commands import shared
from grow.common import rc_config
from grow.pod import pod as grow_pod


CFG = rc_config.RC_CONFIG.prefixed('grow.build')


# pylint: disable=too-many-locals
@click.command()
@shared.pod_path_argument
@shared.out_dir_option(CFG)
def build(pod_path, out_dir):
    """Generates static files and writes them to a local destination."""
    root_path = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = grow_pod.Pod(root_path)
    out_dir = out_dir or os.path.join(root_path, 'build')

    print('Root: {}'.format(pod.root_path))
    print('Out Dir: {}'.format(out_dir))

    return result.CommandResult(pod=pod)
