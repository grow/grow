from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--include-obsolete/--no-include-obsolete', default=False,
              is_flag=True,
              help='Whether to include obsolete messages. If false, obsolete'
                   ' messages will be removed from the catalog template. By'
                   ' default, Grow cleans obsolete messages from the catalog'
                   ' template.')
@click.option('--localized/--no-localized', default=False, is_flag=True,
              help='Whether to create localized message catalogs. Use this'
                   ' option if content varies by locale.')
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
@click.option('--fuzzy/--no-fuzzy', default=False, is_flag=True,
              help='Whether to include fuzzy translations.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to analyze when creating template catalogs'
                   ' that contain only untranslated messages. This option is'
                   ' only applicable when using --missing.')
@click.option('--path', type=str, multiple=True,
              help='Which paths to extract strings from. By default, all paths'
                   ' are extracted. This option is useful if you\'d like to'
                   ' generate a partial messages file representing just a'
                   ' specific set of files.')
@click.option('-o', type=str, default=None,
              help='Where to write the extracted translation catalog. The path'
                   ' must be relative to the pod\'s root. This option is'
                   ' only applicable when using --missing.')
@click.option('--include-header', default=False, is_flag=True,
              help='Whether to preserve headers at the beginning of catalogs.')
@click.option('--outdir', type=str, default=None,
              help='Where to write extracted localized translation catalogs.'
                   ' The path must be relative to the pod\'s root. This option'
                   ' is only applicable when using both --localized and'
                   ' --missing.')
@click.option('-f', default=False, is_flag=True,
              help='Whether to force an update when writing localized, missing'
                   ' message catalogs. This option is only applicable when'
                   ' using both --localized and --missing.')
def extract(pod_path, init, update, missing, locale, o, fuzzy,
            include_obsolete, localized, path, include_header, outdir, f):
  """Extracts tagged messages from source files into a template catalog."""
  if path and o is None and outdir is None:
    raise click.BadOptionUsage(
        '--path', '--path must be used in conjunction with --missing.')
  if missing and o is None and not localized and not outdir:
    raise click.BadOptionUsage('-o', 'Must specify -o when using --missing.')
  if missing and localized and not outdir:
    raise click.BadOptionUsage(
        '--outdir',
        'Must specify --outdir when using both --localized and --missing.')
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  if outdir and pod.file_exists(outdir) and not f:
    raise click.UsageError(
        '{} exists. You must specify a directory that does not exist, or '
        'use the "-f" flag, which will force update catalogs within the '
        'specified directory.'.format(outdir))
  catalogs = pod.get_catalogs(template_path=o)
  catalogs.extract(include_obsolete=include_obsolete, localized=localized,
                   paths=path, include_header=include_header, locales=locale)
  if missing:
    locales = _validate_locales(catalogs.list_locales(), locale)
    if not path:
      catalogs.update(locales=locale)
    catalogs.extract_missing(locales, out_path=o, use_fuzzy=fuzzy, paths=path,
                             include_header=include_header, outdir=outdir)
    return
  if localized or missing:
    return
  if init:
    locales = _validate_locales(pod.list_locales(), locale)
    text = 'Initializing {} empty translation catalogs.'
    pod.logger.info(text.format(len(locales)))
    catalogs.init(locales=locales, include_header=include_header)
    return
  if update:
    locales = _validate_locales(catalogs.list_locales(), locale)
    text = 'Updating {} catalogs with extracted messages.'
    pod.logger.info(text.format(len(locales)))
    catalogs.update(locales=locales, include_header=include_header)


def _validate_locales(valid_locales, locales):
  valid_locales = sorted(valid_locales)
  for each in locales:
    if each not in valid_locales:
      text = ('{} is not a valid translation catalog locale. '
              'Valid locales are: {}')
      raise ValueError(text.format(each, ', '.join(valid_locales)))
  return locales or valid_locales
