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
@click.option('-o', type=str, default=None,
              help='Where to write the extracted translation catalog. The path'
                   ' must be relative to the pod\'s root.')
def extract(pod_path, init, update, missing, locale, o):
  """Extracts tagged messages from source files into a template catalog."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  catalogs = pod.get_catalogs()
  if o is not None:
    # TODO(jeremydw): Refactor this to avoid setting a property.
    catalogs.template_path = o
  if missing:
    catalogs.extract_missing(locale)
    return
  catalogs.extract()
  if init:
    locales = pod.list_locales()
    pod.logger.info('Initializing {} empty translation catalogs.'.format(len(locales)))
    catalogs.init(locales=locales)
    return
  if update:
    locales = catalogs.list_locales()
    pod.logger.info('Updating {} catalogs with extracted messages.'.format(len(locales)))
    catalogs.update(locales=locales)
