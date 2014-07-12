"""Translates the pod message catalog using machine translation.

Usage: grow machine_translate [options] --locale=<locale>... [<pod_path>]

  --help
  --locale=<locale>  Locale(s) to translate
"""

from docopt import docopt
from grow.pods import pods
from grow.pods import storage
from xtermcolor import colorize
import multiprocessing
import os


if __name__ == '__main__':
  multiprocessing.freeze_support()
  args = docopt(__doc__)
  root = os.path.abspath(os.path.join(os.getcwd(), args['<pod_path>'] or '.'))
  pod = pods.Pod(root, storage=storage.FileStorage)

  translations = pod.get_translations()
  translations.extract()
  for locale in args['--locale']:
    translation = translations.get_translation(locale)
    translation.update_catalog()
    translation.machine_translate()

  print ''
  print colorize('  WARNING! Use machine translations with caution.', ansi=197)
  print colorize('  Machine translations are not intended for use in production.', ansi=197)
  print ''
