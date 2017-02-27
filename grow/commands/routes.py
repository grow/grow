from grow.pods import pods
from grow.pods import storage
import click
import collections
import os


@click.command()
@click.argument('pod_path', default='.')
def routes(pod_path):
    """Lists routes handled by a pod."""
    root = os.path.abspath(os.path.join(os.getcwd(), pod_path))
    pod = pods.Pod(root, storage=storage.FileStorage)
    routes = pod.get_routes()
    out = []
    controllers_to_paths = collections.defaultdict(set)
    for route in routes:
        name = str(route.endpoint)
        paths = route.endpoint.list_concrete_paths()
        controllers_to_paths[name].update(paths)
    for controller, paths in controllers_to_paths.iteritems():
        paths = sorted(paths)
        if len(paths) > 1 or True:
            out.append(controller)
            for path in paths:
                out.append('  {}'.format(path))
        else:
            out.append(paths[0])
        out.append('')
    click.echo_via_pager('\n'.join(out))
