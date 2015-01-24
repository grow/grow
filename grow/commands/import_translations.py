from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--source', type=click.Path(), required=True,
              help='Path to source (either zip file or directory).')
def import_translations(pod_path, source):
  """Imports translations from an external source."""
  source = os.path.expanduser(source)
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.catalogs.import_translations(source)
