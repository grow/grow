"""Generates static files and dumps them to a local destination.

Usage: grow build [options] [<pod_path>]

  --help
  --out_dir  Where to output built files
"""

from docopt import docopt
from grow.common import utils
from grow.deployments.destinations import local as local_destination
from grow.deployments.stats import stats
from grow.pods import pods
from grow.pods import storage
import os


if __name__ == '__main__':
  args = docopt(__doc__)
  root = os.path.abspath(os.path.join(os.getcwd(), args['<pod_path>'] or '.'))
  out_dir = args['--out_dir'] or os.path.join(root, 'build')
  pod = pods.Pod(root, storage=storage.FileStorage)
  paths_to_contents = pod.dump()
  repo = utils.get_git_repo(pod.root)
  config = local_destination.Config(out_dir=out_dir)
  stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
  destination = local_destination.LocalDestination(config, run_tests=False)
  destination.deploy(paths_to_contents, stats=stats_obj, repo=repo, confirm=False)
