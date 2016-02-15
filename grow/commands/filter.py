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
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to analyze when creating template catalogs'
                   ' that contain only untranslated messages. This option is'
                   ' only applicable when using --untranslated.')
@click.option('--path', type=str, multiple=True,
              help='Which paths to extract strings from. By default, all paths'
                   ' are extracted. This option is useful if you\'d like to'
                   ' generate a partial messages file representing just a'
                   ' specific set of files.')
@click.option('-o', type=str, default=None,
              help='Where to write the extracted translation catalog. The path'
                   ' must be relative to the pod\'s root.')
@click.option('--include-header', default=False, is_flag=True,
              help='Whether to preserve headers at the beginning of catalogs.')
@click.option('--out_dir', type=str, default=None,
              help='Where to write extracted localized translation catalogs.'
                   ' The path must be relative to the pod\'s root. This option'
                   ' is only applicable when using --localized.')
@click.option('-f', default=False, is_flag=True,
              help='Whether to force an update when writing localized message'
                   ' catalogs.')
def filter(pod_path, locale, o, include_obsolete, localized, path,
           include_header, out_dir, f):
    """Filters untranslated messages from catalogs into new catalogs."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    catalogs = pod.get_catalogs()
    if not locale:
        locale = catalogs.list_locales()
    if out_dir and pod.file_exists(out_dir) and not f:
        raise click.UsageError(
            '{} exists. You must specify a directory that does not exist, or '
            'use the "-f" flag, which will force update catalogs within the '
            'specified directory.'.format(out_dir))
    catalogs.filter(out_path=o, out_dir=out_dir,
                    include_obsolete=include_obsolete,
                    localized=localized, paths=path,
                    include_header=include_header, locales=locale)
