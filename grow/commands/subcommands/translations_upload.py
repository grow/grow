"""Subommand for uploading translations to a remote source."""

import os
import click
from grow.commands import shared
from grow.commands.subcommands.translations_extract import validate_locales
from grow.common import rc_config
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.translations.upload')


@click.command(name='upload')
@shared.pod_path_argument
@click.option('--force/--noforce', '-f', default=CFG.get('force', False), is_flag=True,
              help='Whether to skip the prompt prior to uploading.')
@click.option('--update-acl', default=False, is_flag=True,
              help='Whether to update the ACL on uploaded resources'
                   ' instead of uploading new translation files.')
@click.option('--download/--no-download', '-d', default=CFG.get('download', True),
              help='Whether to download any existing translations prior'
                   ' to uploading.')
@click.option('--extract/--no-extract', '-x', default=CFG.get('extract', True),
              help='Whether to extract translations prior to uploading.')
@click.option('--prune', default=False, is_flag=True,
              help='Whether to remove obsolete messages from spreadsheet.'
                   ' Normally message may be removed and readded periodically'
                   ' so they are not removed, but can be removed to clean up'
                   ' translations but cannot be retrieved once pruned.')
@click.option('--update-meta', default=False, is_flag=True,
              help='Whether to update the meta information for the uploaded'
                   ' resources instead of uploading new translation files.'
                   ' This updates properties that are not directly related to'
                   ' the translation data, such as styling or filters')
@shared.locale_option(
    help_text='Which locale(s) to upload. If unspecified,'
              ' translations for all catalogs will be uploaded.')
@shared.service_option
@shared.reroute_option(CFG)
def translations_upload(pod_path, locale, force, service, update_acl,
                        download, extract, prune, update_meta, use_reroute):
    """Uploads translations to a translation service."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    translator = pod.get_translator(service)

    if not translator:
        raise click.ClickException('No translators specified in podspec.yaml.')

    if update_acl:
        translator.update_acl(locales=locale)
        return

    if update_meta:
        translator.update_meta(locales=locale)
        return

    if download:
        translator.download(locales=locale)

    if extract:
        include_obsolete, localized, include_header, use_fuzzy_matching, = \
            pod.catalogs.get_extract_config()
        catalogs = pod.get_catalogs()
        locales = validate_locales(pod.list_locales(), locale)
        catalogs.extract(include_obsolete=include_obsolete, localized=localized,
                         include_header=include_header,
                         use_fuzzy_matching=use_fuzzy_matching, locales=locales)
        if not localized:
            catalogs.update(locales=locales, include_header=include_header,
                            use_fuzzy_matching=use_fuzzy_matching)

    with pod.profile.timer('grow_translations_upload'):
        translator.upload(locales=locale, force=force,
                          verbose=True, prune=prune)
    return pod
