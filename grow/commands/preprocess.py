from grow.common import utils
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--all', '-A', 'run_all', is_flag=True, default=False,
              help='Whether to run all preprocessors, even if a preprocessor'
                   ' has autorun disabled.')
@click.option('--preprocessor', '-p', type=str, multiple=True,
              help='Which preprocessor to run. Preprocessors controlled by'
                   ' the preprocess command must have names.')
def preprocess(pod_path, preprocessor, run_all):
  """Runs preprocessors."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  pod.preprocess(preprocessor, run_all=run_all)
