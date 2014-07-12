"""Validates a pod and runs its tests.

Usage: grow test [options] [<pod_path>]

  --help
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

  raise NotImplementedError()
