from grow.deployments import stats as stats_lib
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--full/--no-full', '-f', is_flag=True, default=False,
              help='Whether to show full stats. By default, only '
                   'short stats are displayed. Short stats do not '
                   'require a build and may be faster to generate.')
def stats(pod_path, full):
    """Displays statistics about the pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    try:
        stats = stats_lib.Stats(pod, full=full)
        click.echo_via_pager('\n\n'.join(stats.to_tables()))
    except pods.Error as e:
        raise click.ClickException(str(e))
