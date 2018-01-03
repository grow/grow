"""Subcommand for running machine translation on a pod."""

import os
import click
from grow.common import colors
from grow.common import rc_config
from grow.commands import shared
from grow.pods import pods
from grow import storage


CFG = rc_config.RC_CONFIG.prefixed('grow.translations.machine')


@click.command(name='machine')
@shared.pod_path_argument
@shared.locale_option(help_text='Locales to translate.')
@shared.reroute_option(CFG)
def translations_machine(pod_path, locale, use_reroute):
    """Translates the pod message catalog using machine translation."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage, use_reroute=use_reroute)
    with pod.profile.timer('grow_translations_machine'):
        pod.catalogs.extract()
        for identifier in locale:
            catalog = pod.catalogs.get(identifier)
            catalog.update()
            catalog.machine_translate()
        pod.logger.info(colors.stylize(
            'WARNING! Use machine translations with caution.', colors.CAUTION))
        pod.logger.info(colors.stylize(
            'Machine translations are not intended for use in production.', colors.CAUTION))
    return pod
