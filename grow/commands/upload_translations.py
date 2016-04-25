from grow.common import utils
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('translator_name', required=False, default='default')
@click.argument('pod_path', default='.')
@click.option('--locale', type=str, multiple=True,
              help='Which locale(s) to upload. If unspecified,'
                   ' translations for all catalogs will be uploaded.')
@click.option('--force/--noforce', '-f', default=False, is_flag=True,
              help='Whether to skip the prompt prior to uploading.')
def upload_translations(translator_name, pod_path, locale, force):
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translator = pod.get_translator(translator_name)
    stats = translator.upload(locales=locale, force=force, verbose=True)
