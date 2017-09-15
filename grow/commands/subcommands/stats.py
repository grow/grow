"""Subcommand for displaying pod stats."""

import os
import click
from grow.commands import shared
from grow.deployments import stats as stats_lib
from grow.pods import pods
from grow.pods import storage


@click.command()
@shared.pod_path_argument
@click.option('--full/--no-full', '-f', is_flag=True, default=False,
              help='Whether to show full stats. By default, only '
                   'short stats are displayed. Short stats do not '
                   'require a build and may be faster to generate.')
def stats(pod_path, full):
    """Displays statistics about the pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    try:
        with pod.profile.timer('grow_stats'):
            pod_stats = stats_lib.Stats(pod, full=full)
            click.echo_via_pager('\n\n'.join(pod_stats.to_tables()))
    except pods.Error as err:
        raise click.ClickException(str(err))
    return pod
