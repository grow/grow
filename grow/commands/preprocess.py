from grow.common import utils
from grow.deployments.destinations import local as local_destination
from grow.deployments.stats import stats
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--preprocessor', '-p', type=str, multiple=True,
              help='Which preprocessor to run. Preprocessors controlled by'
                   ' the preprocess command must have names.')
def preprocess(pod_path, preprocessor):
  """Runs preprocessors."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.preprocess(preprocessor)
