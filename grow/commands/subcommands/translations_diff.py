"""Subcommand for diffing two directories of translation catalogs."""

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
@click.option('--translations', '-t', help='Path to the other translations directory to diff.')
@click.option('--out_dir', '-o', help='Where to write the diffs.')
def translations_diff(pod_path, translations, out_dir):
    """Diffs a translations directory with another."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translations = os.path.join(translations, 'messages.pot')
    other_catalogs = pod.get_catalogs(translations)
    pod.catalogs.diff(other_catalogs, out_dir)
    return pod
