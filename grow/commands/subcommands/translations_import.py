"""Subcommand for importing translations."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.translations.import')


@click.command(name='import')
@shared.pod_path_argument
@click.option('--source', type=click.Path(), required=True,
              help='Path to source (either zip file, directory, or file).')
@shared.include_obsolete_option(CFG)
@shared.locale_option(
    help_text='Locale of the message catalog to import. This option is'
              ' only applicable when --source is a .po file.', multiple=False)
@shared.reroute_option(CFG)
def translations_import(pod_path, source, locale, include_obsolete, use_reroute):
    """Imports translations from an external source."""
    if source.endswith('.po') and locale is None:
        text = 'Must specify --locale when --source is a .po file.'
        raise click.ClickException(text)
    if not source.endswith('.po') and locale is not None:
        text = 'Cannot specify --locale when --source is not a .po file.'
        raise click.ClickException(text)
    source = os.path.expanduser(source)
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    if not pod.exists:
        raise click.ClickException('Pod does not exist: {}'.format(pod.root))
    with pod.profile.timer('translations_grow_i'):
        pod.catalogs.import_translations(
            source, locale=locale, include_obsolete=include_obsolete)
    return pod
