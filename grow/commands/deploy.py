from grow.common import utils
from grow.deployments.destinations import base
from grow.deployments.stats import stats
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('deployment_name')
@click.argument('pod_path', default='.')
@click.option('--build/--nobuild', default=True, is_flag=True,
              help='Whether to build prior to deployment.')
@click.option('--confirm/--noconfirm', '-c/-f', default=True, is_flag=True,
              help='Whether to confirm prior to deployment.')
@click.option('--test/--notest', default=True, is_flag=True,
              help='Whether to run deployment tests.')
@click.option('--test_only', default=False, is_flag=True,
              help='Only run the deployment tests.')
@click.option('--login', default=False, is_flag=True,
              help='Whether to log into deployment then quit.')
def deploy(deployment_name, pod_path, build, confirm, test, test_only, login):
  """Deploys a pod to a destination."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  try:
    pod = pods.Pod(root, storage=storage.FileStorage)
    deployment = pod.get_deployment(deployment_name)
    if login:
      deployment.login(reauth=True)
      return
    if build:
      pod.preprocess()
    # Set the environment information for the pod based on the deployment.
    pod.env = deployment.get_env()
    if test_only:
      deployment.test()
      return
    paths_to_contents = pod.dump()
    repo = utils.get_git_repo(pod.root)
    stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
    deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                      confirm=confirm, test=test)
  except base.Error as e:
    raise click.ClickException(str(e))
  except pods.Error as e:
    raise click.ClickException(str(e))
