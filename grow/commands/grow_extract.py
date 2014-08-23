"""Extracts a pod's translations into messages files.

Usage: grow extract [options] [<pod_path>]

  --help
  --init  Init catalogs (wipes out existing translations)
"""

from docopt import docopt
from grow.pods import pods
from grow.pods import storage
import multiprocessing
import os


if __name__ == '__main__':
  multiprocessing.freeze_support()
  args = docopt(__doc__)
  root = os.path.abspath(os.path.join(os.getcwd(), args['<pod_path>'] or '.'))
  pod = pods.Pod(root, storage=storage.FileStorage)

  translations = pod.get_translations()
  translations.extract()
  locales = pod.list_locales()
  if not locales:
    logging.info('No pod-specific locales defined, '
                 'skipped generating locale-specific catalogs.')
  else:
    if args['--init']:
      translations.init_catalogs(locales)
    else:
      translations.update_catalogs(locales)
