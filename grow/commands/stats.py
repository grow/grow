from grow.common import utils
from grow.deployments.destinations import local as local_destination
from grow.deployments.stats import stats as stats_lib
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
def stats(pod_path):
    """Displays statistics about the pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    try:
        stats = stats_lib.Stats(pod)
        click.echo_via_pager('\n\n'.join(stats.to_tables()))
    except pods.Error as e:
        raise click.ClickException(str(e))
