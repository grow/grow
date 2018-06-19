"""Build pods into static deployments."""

import os
import click
from grow.commands import result
from grow.commands import shared
from grow.common import rc_config


CFG = rc_config.RC_CONFIG.prefixed('grow.build')


# pylint: disable=too-many-locals
@click.command()
@shared.pod_path_argument
@shared.out_dir_option(CFG)
def build(pod_path, out_dir):
    """Generates static files and writes them to a local destination."""
    cmd_result = result.CommandResult()
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    out_dir = out_dir or os.path.join(root, 'build')

    print('Root: {}'.format(root))
    print('Out Dir: {}'.format(out_dir))

    return cmd_result
