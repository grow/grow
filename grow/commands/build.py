from grow.common import utils
from grow.deployments.destinations import local as local_destination
from grow.deployments.stats import stats
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--out_dir', help='Where to output built files.')
def build(pod_path, out_dir):
  """Generates static files and dumps them to a local destination."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  out_dir = out_dir or os.path.join(root, 'build')
  pod = pods.Pod(root, storage=storage.FileStorage)
  try:
    paths_to_contents = pod.dump()
    repo = utils.get_git_repo(pod.root)
    config = local_destination.Config(out_dir=out_dir)
    stats_obj = stats.Stats(pod, paths_to_contents=paths_to_contents)
    destination = local_destination.LocalDestination(config, run_tests=False)
    destination.deploy(paths_to_contents, stats=stats_obj, repo=repo, confirm=False)
  except pods.Error as e:
    raise click.ClickException(str(e))
