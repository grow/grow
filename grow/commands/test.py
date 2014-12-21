from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
def test(pod_path):
  """Runs tests."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  try:
    click.echo(pod.test())
  except pods.Error as e:
    raise click.ClickException(str(e))
