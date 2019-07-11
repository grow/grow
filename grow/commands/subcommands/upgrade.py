"""Subcommand for upgrading grow."""

import os
import click
from grow.commands import shared
from grow.common import config
from grow.pods import pods
from grow.sdk import updater
from grow import storage


@click.command()
@shared.pod_path_argument
def upgrade(pod_path):
    """Check for and upgrade grow when available."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    try:
        pod = pods.Pod(root, storage=storage.FileStorage)
        with pod.profile.timer('grow_upgrade'):
            pod.logger.info('Checking for newer versions of grow.')
            update_checker = updater.Updater(pod)
            if not update_checker.check_for_updates(force=True):
                pod.logger.info(
                    'No updates found. Running Grow v{}'.format(config.VERSION))
    except pods.Error as err:
        raise click.ClickException(str(err))
    return pod
