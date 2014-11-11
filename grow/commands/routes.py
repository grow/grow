from grow.pods import commands
from grow.pods import pods
from grow.pods import storage
import click
import logging
import os


@click.command()
@click.argument('pod_path', default='.')
def routes(pod_path):
  """Lists routes handled by a pod."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  routes = pod.get_routes()
  logging.info(routes.to_message())
