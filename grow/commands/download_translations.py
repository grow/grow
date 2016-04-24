from grow.common import utils
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('translator_name', required=False, default='default')
@click.argument('pod_path', default='.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to download. If unspecified,'
                   ' translations for all locales will be downloaded.')
def download_translations(translator_name, pod_path, locale):
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translator = pod.get_translator(translator_name)
    translator.download(locales=locale)
