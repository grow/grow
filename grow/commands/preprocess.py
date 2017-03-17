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
              help='Name of preprocessor to run. Preprocessors controlled by'
                   ' the preprocess command must have names or tags.')
@click.option('--tag', '-t', type=str, multiple=True,
              help='Tags of preprocessors to run. Preprocessors controlled by'
                   ' the preprocess command must have names or tags.')
@click.option('--ratelimit', type=int,
              help='Limit the execution speed of preprocessors. Grow will '
                   'sleep for X seconds between running each preprocessor, '
                   'where X is the value of --ratelimit. This flag can be '
                   'useful when using mulitple Google APIs-based '
                   'preprocessors on the same resource to avoid rate limit '
                   'errors.')
def preprocess(pod_path, preprocessor, run_all, tag, ratelimit):
    """Runs preprocessors."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    pod.preprocess(preprocessor, run_all=run_all, tags=tag, ratelimit=ratelimit)
