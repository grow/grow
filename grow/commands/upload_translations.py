from grow.common import utils
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
@click.option('--translator', '-t', type=str,
              help='Name of the translator to use. This option is only required'
                   ' if more than one translator is configured.')
def upload_translations(pod_path, locale, force, translator):
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    translator_obj = pod.get_translator(translator)
    stats = translator_obj.upload(locales=locale, force=force, verbose=True)
