from grow.pods import pods
from grow.pods import storage
from grow.conversion import content_locale_split
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--type', type=click.Choice(['content_locale_split']))
def convert(pod_path, type):
    """Converts pod files from an earlier version of Grow."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)

    if type == 'content_locale_split':
        content_locale_split.Converter.convert(pod)
    else:
        raise click.UsageError(
            'Unable to convert files without a --type option.\n'
            'Run `grow convert --help` to see valid --type values.')
