from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--init/--no-init', default=False, is_flag=True,
              help='Whether to create an initial set of empty translation'
                   ' catalogs using the locales configured in podpsec.')
@click.option('--update/--no-update', default=True, is_flag=True,
              help='Whether to update translation catalogs with extracted'
                   ' messages. If false, only a catalog template will be'
                   ' created.')
@click.option('--missing/--no-missing', default=False, is_flag=True,
              help='Whether to create a template catalog that contains only'
                   ' untranslated messages. This option would typically be'
                   ' used to avoid re-requesting translation of existing'
                   ' messages.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to analyze when creating template catalogs'
                   ' that contain only untranslated messages. This option is'
                   ' only applicable when using --missing.')
@click.option('-o', type=str, default='/translations/messages.pot',
              help='Where to write the extracted translation catalog. The path'
                   ' must be relative to the pod\'s root.')
def extract(pod_path, init, update, missing, locale, o):
  """Extracts tagged messages from source files into a template catalog."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.catalogs.extract(template_path=o)
  if init:
    locales = pod.list_locales()
    pod.logger.info('Initializing {} empty translation catalogs.'.format(len(locales)))
    pod.catalogs.init(locales=locales, template_path=o)
    return
  if update:
    locales = pod.catalogs.list_locales()
    pod.logger.info('Updating {} catalogs with extracted messages.'.format(len(locales)))
    pod.catalogs.update(locales=locales, template_path=o)
