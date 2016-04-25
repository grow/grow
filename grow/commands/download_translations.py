from grow.common import utils
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to download. If unspecified,'
                   ' translations for all locales will be downloaded.')
@click.option('--translator', '-t', type=str,
              help='Name of the translator to use. This option is only required'
                   ' if more than one translator is configured.')
def download_translations(pod_path, locale, translator):
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translator_obj = pod.get_translator(translator)
    translator_obj.download(locales=locale)
