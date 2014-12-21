from grow.pods import pods
from grow.pods import storage
import click
import os


@click.command()
@click.argument('pod_path', default='.')
def routes(pod_path):
  """Lists routes handled by a pod."""
  root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
  pod = pods.Pod(root, storage=storage.FileStorage)
  routes = pod.get_routes()
  out = []
  for route in routes:
    paths = sorted(route.endpoint.list_concrete_paths())
    if len(paths) > 1 or True:
      out.append(str(route.endpoint))
      for path in paths:
        out.append('  {}'.format(path))
    else:
      out.append(paths[0])
    out.append('')
  click.echo_via_pager('\n'.join(out))
