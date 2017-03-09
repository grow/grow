from grow.pods import pods
from grow.pods import storage
from grow.conversion import *
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--version', help='What version to convert files to.')
def convert(pod_path, version):
    """Converts pod files from an earlier version of Grow."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)

    if version == '0.1.0':
        convert_0_1_0.Converter.convert(pod)
    else:
        raise click.UsageError(
            'Unable to convert files without a valid version to convert to.')
