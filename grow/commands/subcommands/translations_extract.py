"""Subcommand for extracting messages for translation."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.translations import catalog_holder
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.translations.extract')


@click.command(name='extract')
@shared.pod_path_argument
@click.option('--init/--no-init', default=False, is_flag=True,
              help='Whether to create an initial set of empty translation'
                   ' catalogs using the locales configured in podpsec.')
@click.option('--update/--no-update', default=True, is_flag=True,
              help='Whether to update translation catalogs with extracted'
                   ' messages. If false, only a catalog template will be'
                   ' created.')
@click.option('--fuzzy-matching/--no-fuzzy-matching',
              default=CFG.get('fuzzy-matching', None), is_flag=True,
              help='Whether to use fuzzy matching when updating translation'
                   ' catalogs. If --fuzzy-matching is specified, updated'
                   ' catalogs will contain fuzzy-translated messages with the'
                   ' "fuzzy" flag. If --fuzzy-matching is not specified,'
                   ' updated catalogs will contain new messages without fuzzy'
                   ' translations. This flag is set to "false" by default'
                   ' because some translation tools may not remove the "fuzzy"'
                   ' flag from messages even after a translation has been'
                   ' provided.')
@click.option('--audit', default=False, is_flag=True,
              help='Audit content files for all untagged strings instead of'
                   ' actually extracting.')
@click.option('-o', type=str, default=None,
              help='Where to write the extracted translation catalog. The path'
                   ' must be relative to the pod\'s root.')
@shared.include_header_option(CFG)
@shared.include_obsolete_option(CFG)
@shared.locale_option(
    help_text='Which locale(s) to analyze when creating template catalogs'
              ' that contain only untranslated messages. This option is'
              ' only applicable when using --update or --init.')
@shared.localized_option(CFG)
@shared.path_option
@shared.reroute_option(CFG)
def translations_extract(pod_path, init, update, include_obsolete, localized,
                         include_header, locale, fuzzy_matching, audit, path, o, use_reroute):
    """Extracts tagged messages from source files into a template catalog."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    with pod.profile.timer('grow_translations_extract'):
        include_obsolete, localized, include_header, use_fuzzy_matching, = \
            pod.catalogs.get_extract_config(
                include_header=include_header, include_obsolete=include_obsolete,
                localized=localized, use_fuzzy_matching=fuzzy_matching)
        locales = validate_locales(pod.list_locales(), locale)
        catalogs = pod.get_catalogs(template_path=o)
        untagged_strings, extracted_catalogs = \
            catalogs.extract(include_obsolete=include_obsolete, localized=localized,
                             include_header=include_header,
                             use_fuzzy_matching=fuzzy_matching, locales=locales,
                             audit=audit, paths=path, out_path=o)
        if audit:
            tables = catalog_holder.Catalogs.format_audit(
                untagged_strings, extracted_catalogs)
            # NOTE: Should use click.echo_via_pager; but blocked by
            # UnicodeDecodeError issue.
            print tables
            return
        if localized:
            return
        if init:
            text = 'Initializing {} empty translation catalogs.'
            pod.logger.info(text.format(len(locales)))
            catalogs.init(locales=locales, include_header=include_header)
            return
        if update:
            locales = validate_locales(catalogs.list_locales(), locale)
            text = 'Updating {} catalogs with extracted messages.'
            pod.logger.info(text.format(len(locales)))
            catalogs.update(locales=locales, include_header=include_header,
                            use_fuzzy_matching=use_fuzzy_matching)
    return pod


def validate_locales(valid_locales, locales):
    """Validate that the locale is a valid local based on the list of locales."""
    valid_locales = sorted(valid_locales)
    for each in locales:
        if each not in valid_locales:
            text = ('{} is not a valid translation catalog locale. '
                    'Valid locales are: {}')
            valid_locales = [str(locale) for locale in valid_locales]
            raise ValueError(text.format(each, ', '.join(valid_locales)))
    return locales or valid_locales
