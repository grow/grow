from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--source', type=click.Path(), required=True,
              help='Path to source (either zip file, directory, or file).')
@click.option('--locale', type=str,
              help='Locale of the message catalog to import. This option is'
                   ' only applicable when --source is a .po file.')
def import_translations(pod_path, source, locale):
  """Imports translations from an external source."""
  source = os.path.expanduser(source)
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  if not pod.exists():
    raise click.ClickException('Pod does not exist: {}'.format(pod.root))
  pod.catalogs.import_translations(source, locale=locale)
