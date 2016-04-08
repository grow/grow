from grow.common import sdk_utils
from grow.common import utils
from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
@click.option('--gerrit/--no-gerrit', default=None,
              help='Whether to install the Gerrit Code Review commit hook. '
                   'If omitted, Grow will attempt to detect whether there is a '
                   'known Gerrit host amongst the remotes in your repository.')
def install(pod_path, gerrit):
    """Checks whether the pod depends on npm, bower, and gulp and installs them
    if necessary. Then, runs install commands. Also optionally installs the
    Gerrit Code Review commit hook."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    sdk_utils.install(pod, gerrit=gerrit)
