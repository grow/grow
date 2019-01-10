"""Subcommand for converting pod files from earlier grow versions."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage
from grow.conversion import content_locale_split


CFG = rc_config.RC_CONFIG.prefixed('grow.convert')


@click.command()
@shared.pod_path_argument
@click.option('--type', 'convert_type', type=click.Choice(['content_locale_split']))
def convert(pod_path, convert_type):
    """Converts pod files from an earlier version of Grow."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)

    if convert_type == 'content_locale_split':
        content_locale_split.Converter.convert(pod)
    else:
        raise click.UsageError(
            'Unable to convert files without a --type option.\n'
            'Run `grow convert --help` to see valid --type values.')
    return pod
