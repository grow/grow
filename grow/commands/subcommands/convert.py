"""Subcommand for converting pod files from earlier grow versions."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage
from grow.conversion import collection_routing
from grow.conversion import content_locale_split


CFG = rc_config.RC_CONFIG.prefixed('grow.convert')
CONVERT_CHOICES = [
    'content_locale_split',
    'collection_routing',
]


@click.command()
@shared.pod_path_argument
@shared.deployment_option(CFG)
@click.option('--type', 'convert_type', type=click.Choice(CONVERT_CHOICES))
def convert(pod_path, convert_type, deployment):
    """Converts pod files from an earlier version of Grow."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    if deployment:
        deployment_obj = pod.get_deployment(deployment)
        pod.set_env(deployment_obj.config.env)

    if convert_type == 'content_locale_split':
        content_locale_split.Converter.convert(pod)
    elif convert_type == 'collection_routing':
        collection_routing.Converter.convert(pod)
    else:
        raise click.UsageError(
            'Unable to convert files without a --type option.\n'
            'Run `grow convert --help` to see valid --type values.')
    return pod
