"""Subcommand for filtering untranslated messages."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.translations.filter')


@click.command(name='filter')
@shared.pod_path_argument
@click.option('-o', type=str, default=None,
              help='Where to write the extracted translation catalog. The path'
                   ' must be relative to the pod\'s root.')
@click.option('-f', default=CFG.get('force', False), is_flag=True,
              help='Whether to force an update when writing localized message'
                   ' catalogs.')
@shared.include_header_option(CFG)
@shared.include_obsolete_option(CFG)
@shared.locale_option(
    help_text='Which locale(s) to analyze when creating template catalogs'
              ' that contain only untranslated messages. This option is'
              ' only applicable when using --untranslated.')
@shared.localized_option(CFG)
@shared.out_dir_option(
    CFG, help_text=('Where to write extracted localized translation catalogs.'
                    ' The path must be relative to the pod\'s root. This option'
                    ' is only applicable when using --localized.'))
@shared.path_option
@shared.reroute_option(CFG)
def translations_filter(pod_path, locale, o, include_obsolete, localized, path,
                        include_header, out_dir, f, use_reroute):
    """Filters untranslated messages from catalogs into new catalogs."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    with pod.profile.timer('grow_translations_filter'):
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
    return pod
