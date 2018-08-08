"""Subommand for uploading translations to a remote source."""

import os
import click
from grow.commands import shared
from grow.commands.subcommands.translations_extract import validate_locales
from grow.common import rc_config
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.translations.diff')


@click.command(name='diff')
@shared.pod_path_argument
@click.option('--other', help='Path to the translation catalog to diff.')
def translations_diff(pod_path, other):
    """Diffs a translations directory with another."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.catalogs.diff(other)
    return pod
