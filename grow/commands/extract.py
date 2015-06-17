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
                   ' must be relative to the pod\'s root. This option is'
                   ' only applicable when using --missing.')
def extract(pod_path, init, update, missing, locale, o):
  """Extracts tagged messages from source files into a template catalog."""
  if missing and o is None:
    raise click.BadOptionUsage('-o', 'Must specify -o when using --missing.')
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  catalogs = pod.get_catalogs()
  catalogs.extract()
  if missing:
    locales = _validate_locales(catalogs.list_locales(), locale)
    catalogs.update(locales=locale)
    catalogs.extract_missing(locales, out_path=o)
    return
  if init:
    locales = _validate_locales(pod.list_locales(), locale)
    pod.logger.info('Initializing {} empty translation catalogs.'.format(len(locales)))
    catalogs.init(locales=locales)
    return
  if update:
    locales = _validate_locales(catalogs.list_locales(), locale)
    pod.logger.info('Updating {} catalogs with extracted messages.'.format(len(locales)))
    catalogs.update(locales=locales)


def _validate_locales(valid_locales, locales):
  valid_locales = sorted(valid_locales)
  for each in locales:
    if each not in valid_locales:
      text = '{} is not a valid translation catalog locale. Valid locales are: {}'
      raise ValueError(text.format(each, ', '.join(valid_locales)))
  return locales or valid_locales
