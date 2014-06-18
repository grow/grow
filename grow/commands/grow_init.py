"""Initializes a pod using a theme, ready for development.

Usage: grow init [options] <theme_repo> [<pod_path>]

  --help
  -f, --force  Overwrite any existing files and directories in the pod
"""

from docopt import docopt
from grow.pods import pods
from grow.pods import storage
from grow.pods import commands
import os


if __name__ == '__main__':
  args = docopt(__doc__)
  root = os.path.abspath(os.path.join(os.getcwd(), args['<pod_path>'] or '.'))
  pod = pods.Pod(root, storage=storage.FileStorage)
  commands.init(pod, args['<theme_repo>'], force=args['--force'])
