from grow.pods import pods
from grow.pods import storage
from xtermcolor import colorize
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--locale', type=basestring, multiple=True)
def machine_translate(pod_path, locale):
  """Translates the pod message catalog using machine translation."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)

  translations = pod.get_translations()
  translations.extract()
  for locale in locale:
    translation = translations.get_translation(locale)
    translation.update_catalog()
    translation.machine_translate()

  print ''
  print colorize('  WARNING! Use machine translations with caution.', ansi=197)
  print colorize('  Machine translations are not intended for use in production.', ansi=197)
  print ''
