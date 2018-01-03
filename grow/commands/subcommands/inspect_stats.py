"""Subcommand for displaying pod stats."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.deployments import stats as stats_lib
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.inspect.stats')


@click.command(name='stats')
@shared.pod_path_argument
@click.option('--full/--no-full', '-f', is_flag=CFG.get('full', True), default=False,
              help='Whether to show full stats. By default, only '
                   'short stats are displayed. Short stats do not '
                   'require a build and may be faster to generate.')
@shared.reroute_option(CFG)
def inspect_stats(pod_path, full, use_reroute):
    """Displays statistics about the pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    try:
        with pod.profile.timer('grow_inspect_stats'):
            pod_stats = stats_lib.Stats(pod, full=full)
            click.echo_via_pager('\n\n'.join(pod_stats.to_tables()))
    except pods.Error as err:
        raise click.ClickException(str(err))
    return pod
