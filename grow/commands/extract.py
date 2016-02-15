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
@click.option('--include-header', default=False, is_flag=True,
              help='Whether to preserve headers at the beginning of catalogs.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to analyze when creating template catalogs'
                   ' that contain only untranslated messages. This option is'
                   ' only applicable when using --update or --init.')
@click.option('--fuzzy-matching/--no-fuzzy-matching', default=False,
              is_flag=True,
              help='Whether to use fuzzy matching when updating translation'
                   ' catalogs. If --fuzzy-matching is specified, updated'
                   ' catalogs will contain fuzzy-translated messages with the'
                   ' "fuzzy" flag. If --fuzzy-matching is not specified,'
                   ' updated catalogs will contain new messages without fuzzy'
                   ' translations. This flag is set to "false" by default'
                   ' because some translation tools may not remove the "fuzzy"'
                   ' flag from messages even after a translation has been'
                   ' provided.')
def extract(pod_path, init, update, include_obsolete, localized,
            include_header, locale, fuzzy_matching):
    """Extracts tagged messages from source files into a template catalog."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    catalogs = pod.get_catalogs()
    catalogs.extract(include_obsolete=include_obsolete, localized=localized,
                     include_header=include_header,
                     use_fuzzy_matching=fuzzy_matching)
    if localized:
        return
    if init:
        locales = validate_locales(pod.list_locales(), locale)
        text = 'Initializing {} empty translation catalogs.'
        pod.logger.info(text.format(len(locales)))
        catalogs.init(locales=locales, include_header=include_header)
        return
    if update:
        locales = validate_locales(catalogs.list_locales(), locale)
        text = 'Updating {} catalogs with extracted messages.'
        pod.logger.info(text.format(len(locales)))
        catalogs.update(locales=locales, include_header=include_header,
                        use_fuzzy_matching=fuzzy_matching)


def validate_locales(valid_locales, locales):
    valid_locales = sorted(valid_locales)
    for each in locales:
        if each not in valid_locales:
            text = ('{} is not a valid translation catalog locale. '
                    'Valid locales are: {}')
            valid_locales = [str(locale) for locale in valid_locales]
            raise ValueError(text.format(each, ', '.join(valid_locales)))
    return locales or valid_locales
