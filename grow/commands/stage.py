from grow.common import utils
from grow.deployments.destinations import base
from grow.deployments.destinations import webreview_destination
from grow.deployments.stats import stats
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--preprocess/--no-preprocess', default=True, is_flag=True,
              help='Whether to run preprocessors.')
@click.option('--remote', required=True,
              help='WebReview remote address (example: '
                   ' example.com/owner/project).')
@click.pass_context
def stage(context, pod_path, remote, preprocess):
  """Stages a build on a WebReview server."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  auth = context.parent.params.get('auth')
  try:
    pod = pods.Pod(root, storage=storage.FileStorage)
    dest_class = webreview_destination.WebReviewDestination
    deployment = dest_class(dest_class.Config(remote=remote))
    if auth:
      deployment.login(auth)
    pod.preprocess()
    repo = utils.get_git_repo(pod.root)
    paths_to_contents = deployment.dump(pod)
    stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
    deployment.deploy(paths_to_contents, stats=stats_obj, repo=repo,
                      confirm=False, test=False)
  except base.Error as e:
    raise click.ClickException(str(e))
  except pods.Error as e:
    raise click.ClickException(str(e))
