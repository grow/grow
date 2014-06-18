"""Deploys a pod to a destination.

Usage: grow deploy [options] [<nickname>] [<pod_path>]

  --help
  --skip_confirm  Skip confirm prior to deployment
  --test_only     Only run the deployment tests
"""

from docopt import docopt
from grow.deployments.stats import stats
from grow.pods import pods
from grow.pods import storage
import os


if __name__ == '__main__':
  args = docopt(__doc__)
  root = os.path.abspath(os.path.join(os.getcwd(), args['<pod_path>'] or '.'))
  deployment_name = args['<nickname>'] || 'default'

  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.preprocess()

  # Set the environment information for the pod based on the deployment.
  deployment = pod.get_deployment(deployment_name)
  pod.env = deployment.get_env()

  if args['--test_only']:
    deployment.test()
  else:
    paths_to_contents = pod.dump()
    repo = _get_git_repo(pod.root)
    stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
    deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                      confirm=args['--skip_confirm'] == False)
