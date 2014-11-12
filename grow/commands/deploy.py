from grow.deployments.stats import stats
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.argument('deployment_name', default='default')
@click.option('--skip_confirm', default=False, help='Skip confirm prior to deployment.')
@click.option('--test_only', default=False, help='Only run the deployment tests.')
def deploy(pod_path, deployment_name, skip_confirm, test_only):
  """Deploys a pod to a destination."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))

  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.preprocess()

  # Set the environment information for the pod based on the deployment.
  deployment = pod.get_deployment(deployment_name)
  pod.env = deployment.get_env()

  if test_only:
    deployment.test()
  else:
    paths_to_contents = pod.dump()
    repo = _get_git_repo(pod.root)
    stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
    deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                      confirm=skip_confirm)
