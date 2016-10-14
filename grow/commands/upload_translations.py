from grow.common import utils
from grow.commands.extract import validate_locales
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to upload. If unspecified,'
                   ' translations for all catalogs will be uploaded.')
@click.option('--force/--noforce', '-f', default=False, is_flag=True,
              help='Whether to skip the prompt prior to uploading.')
@click.option('--service', '-s', type=str,
              help='Name of the translator service to use. This option is'
                   ' only required if more than one service is configured.')
@click.option('--update-acl', default=False, is_flag=True,
              help='Whether to update the ACL on uploaded resources'
                   ' instead of uploading new translation files.')
@click.option('--download', '-d', default=True, is_flag=True,
              help='Whether to download any existing translations prior'
                   ' to uploading.')
@click.option('--extract', '-x', default=True, is_flag=True,
              help='Whether to extract translations prior to uploading.')
@click.option('--include-obsolete/--no-include-obsolete', default=None,
            is_flag=True,
            help='Whether to include obsolete messages. If false, obsolete'
                 ' messages will be removed from the upload. By'
                 ' default, Grow cleans obsolete messages from the upload')
def upload_translations(pod_path, locale, force, service, update_acl,
                        download, extract, include_obsolete):
    """Uploads translations to a translation service."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translator = pod.get_translator(service)

    if extract:
        include_obsolete, localized, include_header, use_fuzzy_matching, = \
            pod.catalogs.get_extract_config(include_obsolete=include_obsolete)
        catalogs = pod.get_catalogs()
        catalogs.extract(include_obsolete=include_obsolete, localized=localized,
                         include_header=include_header,
                         use_fuzzy_matching=use_fuzzy_matching)
        locales = validate_locales(pod.list_locales(), locale)
        catalogs.update(locales=locales, include_header=include_header,
                        use_fuzzy_matching=use_fuzzy_matching)

    if not translator:
        raise click.ClickException('No translators specified in podspec.yaml.')
    if update_acl:
        translator.update_acl(locales=locale)
    else:
        translator.upload(locales=locale, force=force, verbose=True,
                          download=download, include_obsolete=include_obsolete)
