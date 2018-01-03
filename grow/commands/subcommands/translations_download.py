"""Command for downloading translations from remote source."""

import os
import click
from grow.commands import shared
from grow.common import rc_config
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.translations.download')


@click.command(name='download')
@shared.pod_path_argument
@shared.locale_option(help_text='Which locale(s) to download. If unspecified,'
                                ' translations for all locales will be downloaded.')
@shared.service_option
@shared.include_obsolete_option(CFG)
@shared.reroute_option(CFG)
def translations_download(pod_path, locale, service, include_obsolete, use_reroute):
    """Downloads translations from a translation service."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    with pod.profile.timer('grow_translations_download'):
        translator = pod.get_translator(service)
        translator.download(locales=locale, include_obsolete=include_obsolete)
    return pod
