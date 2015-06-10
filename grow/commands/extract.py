from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--init/--no-init', default=False, is_flag=True,
              help='Whether to create an initial set of empty translation '
                   ' catalogs using the locales configured in podpsec.')
@click.option('--update/--no-update', default=True, is_flag=True,
              help='Whether to update translation catalogs with extracted '
                   ' messages. If false, only a catalog template will be'
                   ' created.')
def extract(pod_path, init, update):
  """Extracts tagged messages from source files into a template catalog."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.catalogs.extract()
  if init:
    locales = pod.list_locales()
    pod.logger.info('Initializing {} empty translation catalogs.'.format(len(locales)))
    pod.catalogs.init(locales)
    return
  if update:
    locales = pod.catalogs.list_locales()
    pod.logger.info('Updating {} catalogs with extracted messages.'.format(len(locales)))
    pod.catalogs.update(locales)
