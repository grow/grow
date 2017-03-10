from grow.pods import pods
from grow.pods import storage
from grow.conversion import *
import click
import os


@click.command()
@click.argument('conversion')
@click.argument('pod_path', default='.')
def convert(conversion, pod_path):
    """Converts pod files from an earlier version of Grow."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)

    if conversion == 'content_locale_split':
        content_locale_split.Converter.convert(pod)
    else:
        raise click.UsageError(
            'Unable to convert files without a conversion to run.')
