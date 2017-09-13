"""Command for downloading translations from remote source."""

import os
import click
from grow.pods import pods
from grow.pods import storage


@click.command()
@click.argument('pod_path', default='.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to download. If unspecified,'
                   ' translations for all locales will be downloaded.')
@click.option('--service', '-s', type=str,
              help='Name of the translator service to use. This option is'
                   ' only required if more than one service is configured.')
def download_translations(pod_path, locale, service):
    """Downloads translations from a translation service."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    with pod.profile.timer('grow_download_translations'):
        translator = pod.get_translator(service)
        translator.download(locales=locale)
    return pod
