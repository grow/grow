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
@click.option('--download/--no-download', '-d', default=True,
              help='Whether to download any existing translations prior'
                   ' to uploading.')
@click.option('--extract/--no-extract', '-x', default=True,
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
def upload_translations(pod_path, locale, force, service, update_acl,
                        download, extract, prune, update_meta):
    """Uploads translations to a translation service."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translator = pod.get_translator(service)

    if update_acl:
        translator.update_acl(locales=locale)
        return

    if update_meta:
        translator.update_meta(locales=locale)
        return

    if extract:
        include_obsolete, localized, include_header, use_fuzzy_matching, = \
            pod.catalogs.get_extract_config()
        catalogs = pod.get_catalogs()
        catalogs.extract(include_obsolete=include_obsolete, localized=localized,
                         include_header=include_header,
                         use_fuzzy_matching=use_fuzzy_matching)
        locales = validate_locales(pod.list_locales(), locale)
        catalogs.update(locales=locales, include_header=include_header,
                        use_fuzzy_matching=use_fuzzy_matching)

    if not translator:
        raise click.ClickException('No translators specified in podspec.yaml.')
    else:
        # TODO Remove the download from the upload arguments to clean it up.
        translator.upload(locales=locale, force=force, verbose=True,
                          download=download, prune=prune)
