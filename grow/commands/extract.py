from grow.pods import pods
from grow.pods import storage
import click
import logging
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--init', default=False, help='Whether to wipe out existing translations.')
def extract(pod_path, init):
  """Extracts translations into messages files."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.catalogs.extract()
  locales = pod.list_locales()
  if not locales:
    logging.info('No pod-specific locales defined, '
                 'skipped generating locale-specific catalogs.')
  else:
    if init:
      pod.catalogs.init(locales)
    else:
      pod.catalogs.update(locales)
